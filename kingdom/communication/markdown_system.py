#!/usr/bin/env python3
"""
Markdown-based Agent Communication System for the Kingdom Project

This module implements markdown-based communication between agents, allowing them
to exchange structured information using markdown files as a communication medium.
This provides a human-readable audit trail and enables agents to collaborate through
shared documents.
"""

import os
import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.base_agent import AgentMessage, MessageType


class MarkdownMessageType(Enum):
    """Types of markdown-based messages"""
    TASK_BRIEF = "task_brief"              # Project/task specifications
    STATUS_REPORT = "status_report"        # Progress updates
    COLLABORATION = "collaboration"        # Joint working documents
    KNOWLEDGE_SHARE = "knowledge_share"    # Information sharing
    DECISION_LOG = "decision_log"          # Decision making records
    MEETING_NOTES = "meeting_notes"        # Agent committee discussions

@dataclass
class MarkdownDocument:
    """Structure for markdown communication documents"""
    id: str
    title: str
    type: MarkdownMessageType
    author_agent_id: str
    participants: List[str]  # Agent IDs involved
    created_at: datetime
    updated_at: datetime
    file_path: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str] = None
    priority: int = 5
    status: str = "active"  # active, archived, obsolete

class MarkdownCommunicationSystem:
    """
    Manages markdown-based communication between agents.
    
    Creates a shared workspace where agents can create, read, and collaborate
    on markdown documents for structured information exchange.
    """
    
    def __init__(self, workspace_path: str = "./kingdom/workspace"):
        self.workspace_path = Path(workspace_path)
        self.documents: Dict[str, MarkdownDocument] = {}
        self.document_index: Dict[str, Set[str]] = {}  # tag -> {doc_ids}
        self.agent_documents: Dict[str, Set[str]] = {}  # agent_id -> {doc_ids}
        self.watchers: Dict[str, Set[str]] = {}  # doc_id -> {agent_ids watching}
        self.change_notifications = asyncio.Queue()
        
        # File system monitoring
        self.file_checksums: Dict[str, str] = {}
        self.monitoring_active = False
        
        self._ensure_workspace_structure()
    
    def _ensure_workspace_structure(self):
        """Create workspace directory structure"""
        directories = [
            "task_briefs",
            "status_reports", 
            "collaboration",
            "knowledge_base",
            "decision_logs",
            "meeting_notes",
            "archive"
        ]
        
        for dir_name in directories:
            dir_path = self.workspace_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def start_monitoring(self):
        """Start file system monitoring for changes"""
        self.monitoring_active = True
        asyncio.create_task(self._monitor_changes())
        print(f"📁 Markdown communication system monitoring: {self.workspace_path}")
    
    async def stop_monitoring(self):
        """Stop file system monitoring"""
        self.monitoring_active = False
    
    async def create_document(self, author_agent_id: str, title: str, 
                            doc_type: MarkdownMessageType, 
                            content: str = "", 
                            participants: List[str] = None,
                            tags: List[str] = None,
                            metadata: Dict[str, Any] = None) -> MarkdownDocument:
        """Create a new markdown communication document"""
        
        doc_id = self._generate_doc_id(title, author_agent_id)
        participants = participants or [author_agent_id]
        tags = tags or []
        metadata = metadata or {}
        
        # Determine file path based on type
        type_dir = self._get_type_directory(doc_type)
        filename = self._sanitize_filename(f"{doc_id}_{title}.md")
        file_path = self.workspace_path / type_dir / filename
        
        # Create document object
        doc = MarkdownDocument(
            id=doc_id,
            title=title,
            type=doc_type,
            author_agent_id=author_agent_id,
            participants=participants,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            file_path=str(file_path),
            content=content,
            metadata=metadata,
            tags=tags
        )
        
        # Write markdown file
        await self._write_markdown_file(doc)
        
        # Register document
        self.documents[doc_id] = doc
        self._update_indexes(doc)
        
        print(f"📝 Created document: {title} ({doc_type.value})")
        return doc
    
    async def update_document(self, doc_id: str, updater_agent_id: str, 
                            new_content: str = None, 
                            new_title: str = None,
                            additional_metadata: Dict[str, Any] = None,
                            add_tags: List[str] = None) -> bool:
        """Update an existing document"""
        
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        # Check permissions (basic - can be enhanced later)
        if updater_agent_id not in doc.participants:
            # Add updater as participant if not already
            doc.participants.append(updater_agent_id)
        
        # Update content
        if new_content is not None:
            # Append update section to preserve history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_section = f"\n\n---\n## Update by {updater_agent_id} - {timestamp}\n\n{new_content}"
            doc.content += update_section
        
        # Update title if provided
        if new_title:
            doc.title = new_title
        
        # Update metadata
        if additional_metadata:
            doc.metadata.update(additional_metadata)
        
        # Add tags
        if add_tags:
            doc.tags.extend([tag for tag in add_tags if tag not in doc.tags])
        
        doc.updated_at = datetime.now()
        
        # Write updated file
        await self._write_markdown_file(doc)
        
        # Update indexes
        self._update_indexes(doc)
        
        # Notify watchers
        await self._notify_watchers(doc_id, f"Document updated by {updater_agent_id}")
        
        print(f"📝 Updated document: {doc.title}")
        return True
    
    async def read_document(self, doc_id: str) -> Optional[MarkdownDocument]:
        """Read a document by ID"""
        return self.documents.get(doc_id)
    
    async def search_documents(self, query: str = None, 
                             doc_type: MarkdownMessageType = None,
                             tags: List[str] = None,
                             author: str = None,
                             participant: str = None) -> List[MarkdownDocument]:
        """Search documents by various criteria"""
        
        results = list(self.documents.values())
        
        # Filter by type
        if doc_type:
            results = [doc for doc in results if doc.type == doc_type]
        
        # Filter by author
        if author:
            results = [doc for doc in results if doc.author_agent_id == author]
        
        # Filter by participant
        if participant:
            results = [doc for doc in results if participant in doc.participants]
        
        # Filter by tags
        if tags:
            results = [doc for doc in results if any(tag in doc.tags for tag in tags)]
        
        # Text search in title and content
        if query:
            query_lower = query.lower()
            results = [doc for doc in results 
                      if query_lower in doc.title.lower() or query_lower in doc.content.lower()]
        
        # Sort by updated_at (most recent first)
        results.sort(key=lambda x: x.updated_at, reverse=True)
        
        return results
    
    async def watch_document(self, doc_id: str, watcher_agent_id: str):
        """Add an agent as a watcher for document changes"""
        if doc_id not in self.watchers:
            self.watchers[doc_id] = set()
        self.watchers[doc_id].add(watcher_agent_id)
    
    async def unwatch_document(self, doc_id: str, watcher_agent_id: str):
        """Remove an agent as a watcher"""
        if doc_id in self.watchers:
            self.watchers[doc_id].discard(watcher_agent_id)
    
    async def archive_document(self, doc_id: str) -> bool:
        """Archive a document (move to archive folder)"""
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        # Move file to archive
        old_path = Path(doc.file_path)
        archive_path = self.workspace_path / "archive" / old_path.name
        
        if old_path.exists():
            old_path.rename(archive_path)
            doc.file_path = str(archive_path)
            doc.status = "archived"
        
        print(f"📦 Archived document: {doc.title}")
        return True
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document completely"""
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        # Remove file
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Remove from indexes
        self._remove_from_indexes(doc)
        
        # Remove from registry
        del self.documents[doc_id]
        
        print(f"🗑️  Deleted document: {doc.title}")
        return True
    
    async def get_agent_documents(self, agent_id: str) -> List[MarkdownDocument]:
        """Get all documents involving a specific agent"""
        return [doc for doc in self.documents.values() 
                if agent_id in doc.participants or doc.author_agent_id == agent_id]
    
    async def create_collaboration_space(self, title: str, 
                                       participating_agents: List[str],
                                       initial_content: str = "") -> MarkdownDocument:
        """Create a collaborative document space for multiple agents"""
        
        if not initial_content:
            initial_content = f"""# {title}
            
## Participants
{chr(10).join([f'- {agent_id}' for agent_id in participating_agents])}

## Collaboration Notes

*This document is for collaborative work between the above agents.*

"""
        
        return await self.create_document(
            author_agent_id=participating_agents[0] if participating_agents else "system",
            title=title,
            doc_type=MarkdownMessageType.COLLABORATION,
            content=initial_content,
            participants=participating_agents,
            tags=["collaboration", "multi-agent"]
        )
    
    async def _write_markdown_file(self, doc: MarkdownDocument):
        """Write document to markdown file with metadata header"""
        
        # Create YAML front matter
        front_matter = {
            'id': doc.id,
            'title': doc.title,
            'type': doc.type.value,
            'author': doc.author_agent_id,
            'participants': doc.participants,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
            'tags': doc.tags,
            'priority': doc.priority,
            'status': doc.status,
            'metadata': doc.metadata
        }
        
        # Write file
        file_content = f"""---
{json.dumps(front_matter, indent=2, default=str)}
---

# {doc.title}

{doc.content}
"""
        
        file_path = Path(doc.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Update checksum for monitoring
        self.file_checksums[doc.file_path] = self._calculate_checksum(file_content)
    
    async def _monitor_changes(self):
        """Monitor workspace for external file changes"""
        while self.monitoring_active:
            try:
                # Check for file changes
                for doc_id, doc in self.documents.items():
                    file_path = Path(doc.file_path)
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        new_checksum = self._calculate_checksum(content)
                        old_checksum = self.file_checksums.get(doc.file_path)
                        
                        if old_checksum and new_checksum != old_checksum:
                            await self._handle_external_change(doc_id, content)
                            self.file_checksums[doc.file_path] = new_checksum
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Error monitoring markdown files: {e}")
                await asyncio.sleep(10)
    
    async def _handle_external_change(self, doc_id: str, new_content: str):
        """Handle external changes to markdown files"""
        if doc_id in self.documents:
            print(f"📝 External change detected in document: {self.documents[doc_id].title}")
            # Here you could parse the new content and update the document object
            # For now, just notify watchers
            await self._notify_watchers(doc_id, "Document externally modified")
    
    async def _notify_watchers(self, doc_id: str, change_description: str):
        """Notify agents watching a document about changes"""
        if doc_id in self.watchers:
            for agent_id in self.watchers[doc_id]:
                notification = {
                    'doc_id': doc_id,
                    'change': change_description,
                    'timestamp': datetime.now().isoformat()
                }
                await self.change_notifications.put((agent_id, notification))
    
    def _update_indexes(self, doc: MarkdownDocument):
        """Update search indexes for a document"""
        # Update tag index
        for tag in doc.tags:
            if tag not in self.document_index:
                self.document_index[tag] = set()
            self.document_index[tag].add(doc.id)
        
        # Update agent document index
        for agent_id in doc.participants + [doc.author_agent_id]:
            if agent_id not in self.agent_documents:
                self.agent_documents[agent_id] = set()
            self.agent_documents[agent_id].add(doc.id)
    
    def _remove_from_indexes(self, doc: MarkdownDocument):
        """Remove document from search indexes"""
        # Remove from tag index
        for tag in doc.tags:
            if tag in self.document_index:
                self.document_index[tag].discard(doc.id)
        
        # Remove from agent index
        for agent_id in doc.participants + [doc.author_agent_id]:
            if agent_id in self.agent_documents:
                self.agent_documents[agent_id].discard(doc.id)
    
    def _get_type_directory(self, doc_type: MarkdownMessageType) -> str:
        """Get directory name for document type"""
        type_dirs = {
            MarkdownMessageType.TASK_BRIEF: "task_briefs",
            MarkdownMessageType.STATUS_REPORT: "status_reports",
            MarkdownMessageType.COLLABORATION: "collaboration", 
            MarkdownMessageType.KNOWLEDGE_SHARE: "knowledge_base",
            MarkdownMessageType.DECISION_LOG: "decision_logs",
            MarkdownMessageType.MEETING_NOTES: "meeting_notes"
        }
        return type_dirs.get(doc_type, "general")
    
    def _generate_doc_id(self, title: str, author_id: str) -> str:
        """Generate unique document ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"{timestamp}_{author_id}_{title_hash}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:96] + ext
        return filename
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of content"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        type_counts = {}
        for doc in self.documents.values():
            type_name = doc.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'documents_by_type': type_counts,
            'total_watchers': sum(len(watchers) for watchers in self.watchers.values()),
            'workspace_path': str(self.workspace_path),
            'monitoring_active': self.monitoring_active
        }


# Integration helper functions

async def create_task_brief(comm_system: MarkdownCommunicationSystem,
                          project_name: str, task_description: str,
                          assigning_agent: str, assigned_agents: List[str],
                          requirements: List[str] = None,
                          deadline: str = None) -> MarkdownDocument:
    """Helper to create a standardized task brief document"""
    
    requirements = requirements or []
    
    content = f"""## Project: {project_name}

### Task Description
{task_description}

### Assigned Agents
{chr(10).join([f'- {agent}' for agent in assigned_agents])}

### Requirements
{chr(10).join([f'- {req}' for req in requirements]) if requirements else "No specific requirements listed."}

### Deadline
{deadline if deadline else "No deadline specified."}

### Status
- [ ] Task assigned
- [ ] Work in progress  
- [ ] Review required
- [ ] Complete

### Notes
*Task brief created by {assigning_agent}*
"""
    
    return await comm_system.create_document(
        author_agent_id=assigning_agent,
        title=f"Task Brief: {project_name}",
        doc_type=MarkdownMessageType.TASK_BRIEF,
        content=content,
        participants=[assigning_agent] + assigned_agents,
        tags=["task", "brief", project_name.lower().replace(" ", "_")]
    )