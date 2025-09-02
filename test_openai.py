#!/usr/bin/env python3
"""Test script to check OpenAI API connectivity"""

import os
import asyncio
from openai import OpenAI

async def test_openai():
    """Test OpenAI API call"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return

    print(f"✅ Found API key: {api_key[:10]}...")

    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client initialized")

    try:
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello"}
            ],
            temperature=0.7,
            max_tokens=100
        )

        print("✅ API call successful!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")

    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai())