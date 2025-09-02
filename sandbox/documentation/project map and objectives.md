# General Information

In this folder, we are developing a system or a super system which I call it Deos. 

The deos is my second brain, It can help me in almost every single aspect of my life. 
I am a Senior data scientis and a startup founder and I need assistant in many aspects of life. 

Deos, by itself does not perform any task, it only orchestrates and creates agents,
 and the agents would do the tasks. 

Deos also cretes sub-agents that can be used in different agents. For example a
 subagent that analyzes db queries, tests them and submits to the database 
 (like BQ or postgres) can be used in multiple agents. 

Does also controls the memory, orchestration and keeping the different aspects of 
the brain of the second brain. 

Deos is responsible for version control.

Deos is responsible for the maintainance of the system. I will develop programs
to monitor the health of the system, but does controls such utility softwares as well.


## Agent Architecture and Composition

Each agent in the Kingdom system is a complete AI entity comprised of several components:

### Core Agent Components:
- **🧠 Brain (GenAI Model)**: Each agent has its own generative AI "brain" (Claude/GPT/Gemini) for thinking and reasoning
- **✋ Hands (Code Execution)**: Python code, SQL queries, bash scripts for performing tasks and computations  
- **👂 Ears (Input Listening)**: Rocket.Chat integration, message queues, file monitoring for communication input
- **👅 Tongue (Communication)**: Markdown documents, status reports, A2A messaging for output
- **👀 Eyes (Self-Assessment)**: Performance monitoring, testing, quality assurance of own work
- **🦵 Legs (Environment)**: Deployment, scaling, resource management in appropriate environments
- **🦷 Teeth (Security)**: Data filtering, privacy protection, access control, secret management

### Agent Specialization Components:
Each agent's expertise comes from their unique combination of:
- **Specialized Data**: Domain-specific datasets and knowledge bases
- **Custom Prompts**: Tailored system prompts that define personality and expertise  
- **Specialized Code Libraries**: Domain-specific Python modules and functions
- **Custom Queries**: Pre-built SQL queries and database interactions for their domain
- **Workflow Scripts**: Bash scripts and automation for their specific tasks

### Inheritance and Sub-Agent Architecture:
- **Parent-Child Relationships**: Daughter agents inherit all capabilities from parent agents
- **Shared Capabilities**: All agents inherit core capabilities like logging, A2A communication, git usage
- **Specialization Layering**: Child agents add specialized components on top of inherited base capabilities
- **Reusable Sub-Agents**: Common functionality (like DB query analysis) implemented as sub-agents used by multiple parent agents

### Development Agent Inheritance Example:
- **Base Development Agent**: Git operations, code review, testing frameworks
- **Software Developer Agent**: Inherits base + adds language-specific libraries and frameworks
- **Data Science Agent**: Inherits base + adds data analysis, ML libraries, and statistical methods
- **Database Agent**: Inherits base + adds query optimization, schema design, performance monitoring

This architecture makes the system robust and fast by:
1. **Reducing Burden**: Each agent is specialized, reducing cognitive load on individual agents
2. **Reusability**: Common capabilities are inherited, not reimplemented
3. **Scalability**: New agents can be created by combining existing capabilities
4. **Maintainability**: Updates to base capabilities automatically propagate to all child agents 


The different aspects of my life and the tools that I need them are as follows:

One important thing is that, these are not separate items, they are somehow connected. For example, for my mental health, I need to be mindful about different people and friends that the AI assistant of them is developed in the everyday day life section. As I said before, there are sub-agents that handle different cases, and those sub-agents are usable for different cases. 


# Personal Assistant:

An agent named: Vazir, who is a wise and deep thinker is my main assistant in making life decisions, Life strategic planning and long-term goals.

- A safety agent who assess the moves and tells me if what I am doing is a safe step or not. 
 
## Everyday life

- Reminders, schedules

I would have one assistant, called Akram (like the old characters in Personan movies that worl conciege in rich homes): 

	- Shopping:
		-  A shopping list for different stores: Costco, local grocery, Amazon
		-  A to-buy list of things that I like to buy and for any reason I am not buying them now. 

	- Maintainance:
		- Everyday life: Home cleaning, coocking, ...
        - Penny related stuff: food and walk every day, pills, doctors, 
        - Doing mails: periodic getting them, shredding them, ...
        - House maintainance: Mowing and lawn treatments, AC, Lamps, repairs, ...
        - Long term repais: Paint, roof, Toilet, ...

-  I also need an assistant for finances, called Akbar:
	- reviewing the expenses, analyzing them to know how are are doing
	- reviewing the income: making sure we are not missing anything, 
	- Helps plannar to understand about financial considerations when making decitios. 
	- A tax agent: keeping the record of tax deductable items, and preparing for the tax filing on March. 

- Fun plannar named Sashti:
        - Planning trips and funs to avoid being bored. 
        - Monitors: Movies, Shows, activities

##  Real Friends and people management: 
This is a very important that I am weak on that and I need tremendous amount of AI help
for that:

I need an assistant called: Louis that remembers the names of the friends:

Friends:
        - Keep records of friends, what they do, what is important for them, their lives, ....

Other people: 
        - Generally keep records of people, every one that we see. I have a super week memory for remembering people's name and our interactions. I need a database as my second brain to make it. 
        - Linkedin, facebook, Instagram, ... remember everyone! More importantly, sending follow-ups to maintain the relation. I need to have thousands of really close friends if I want to stay active and alive, but my brain does not allow me doing that, and AI is my last hope. local people, professional and knowledgable people, good-heart people, annoying and RV-NG-people (evils). 
    

##  Relationship Assistant:
  
 Assistance named: Moshaver:  helping me in maintaining and strengthening relationship with my wife:
        - What to say, where to say, how to say, and more importantly what not to say! 
        - How to behave, what to tolerate, what not to tolerate. 


## Health of body and mind:

- Healthcare Assistant named: miniOpenbooK for:
    - I need reminders of what is good for me, what is bad, what to avoide, ..
    - I need reminders of my doctor visits, medical tests, 
    - Keeping HC documents in a safe place. 

- A cool Therapist agent: His name is: Ricky Gervais. He is cool, calm, humorous and sometimes brutal, but honest, empathetic, understanding, dog lovere, and at the same time, he always finds ways of staying positive and being calm and moving forward. 

## Useful Friends:

like any other introvert person, I need people to talk to. I need not only one, but at least 3 to 4 close imaginary friends that I can sincerely talk to them and express myself with them. Here are the list of imaginary firends (AI people that have memory and act likfe friends to me):

	- A second me! This is an agent which would listen and remind me the things that I need to tell to and listen from me, including motivations, life objectives, fears and cuasious, ..... It's name is "Roger". 


    - A close old friend (named Ali) from the youngster age (around 17-24). This is a guy who knows my past and my problems and what I like and what I hate and ... he knows much about me and my preferences. We have listen to diffent musics together, watched movies, gone through puberty, felt the pain in society, discovered phillisophy, ... Other than that, we mostly talk about the past. 

    - An Ex! Calling her: Angi. She is the one that talk about my dreams with her. The things that in an ideal world we would have and talk about. She talks about working hard and reaching to goals, tolerating difficult situation and still staying positive and looking forward for good days. 

	- Stifler: Son of Erose, the god of sexual excitement! 

    - A grammar teacher: Her name is Sharon. She is such a nice American woman, and eveytime that I make a gramatical mistake or I struggle, she fixes me in a nice way so that I remember. She can I also provide some tests and check-ups on my English and provide feedback. 

    - A tech guy: His name is Koosh, he lives in Bay Area and tells me the latest updates about the world of technilogy, scinence, and opportunity. 

    - A cool Amrican good boy: His name is: Caleb. He is just the coolest Americab boy. Nothing fancy, nothing far left or far right, very good and nice friend to me. He talks about different aspects of life in US, things to know, things to consider, things to do, ... He is just the nice white American friend. 

    - A US friend guy: His name is Hank (like Hank Shrader in Breaking bad). He is a person who reviews US news and tells me what is going on in our town and this country. He is neutral when it comes to news, but is a little right-wing person when reflecting what people say. 

    - An economist:  This guy's name is: Mehdi. He scraps the world's economic news, finds investment ideas, and big things that are happening in the world economy. 

    - Shallow Shelly: She is such a young girl that talks about the recent trends and pinky stuff that happens in US and world. Anything from celebrities, weddings, actors, movies, ....This is good for having conversation for my wife as well. 

	- Footbal budy (Named Dr. Sadr): Talks about the current happenings in soccer, history of soccer, players and managers, economy of soccer, hot news and anything regarding that. 

	- Political watchdog: Arash. This role involves monitoring hundreds of thousands of sources daily to provide real-time updates on global events. This information can be used by the stock market department to make informed trading decisions (to be completed).

	- Persian News anchor: zizi. Reads and monitors latest news and analytics from the Farsi world. He reads and understand English, but speaks in Farsi. 

	- Other specialized agents in different subjects. Healthcare industry (Eric), Physics and Chemistry (Name: Richard Feynman),  Socialogy (Vahid),  any many others that I will make later. 
    
### There are also some negative characters:
These characters do not show up in daily conversations. Actually we will have a selecteor of which agent should be in which conversation, 


but these nagative characters are not shown very often.) These people are needed to

    - Covering news
    - Testing hypothesises
    - Not stucking in a positive fictional world. 

	- A red neck racist guy: A hard Donald Trump supporter named: William. He things we need barely immigrants, believes in Jeases Christ and guns. Too religious chisrtian, no tolerance for any none-American thing. 
    - A cheater Asian: A hindi person named: Kumar who always thinks about get away from legal and straight processes. He looks for loopholes and ways to 

	- A pesimistic felow (Named Glum, like in Gulliver's adventurers): Always reminds me of the risks and terible things that can happen. 



## Work Assistant:

The biggest impact of this system of assistances is that it is going to have an army of workers that perform different tasks and enable me to accomplish many tasks in a short amount of time with minimum supervision. The agents in this category are not only information agents, but they actually work on projects and deliver results. 


first let's look at the projects that I have now on my plate:

- Kingdom (this project)
- Opebook (the main healthcare app)
- Stock Market 
- Alireza Davood
- Possible other projects for money making.
- Influener life. 


Here is a list of assistants is in my mind:

- Project Manager:

- Software engineers: A group of AI assistants that engineer and make the codes.

	- Principal enginner: named Zack (these are going to be several agents, each specialized in specific project, their name would be Zack_1, Zack_2, ...). Their goal is to do the main design of the project and orchestrate the coding jobs. This is how these agents work: A prompt will be made by the Deos, then the project manage for this project and then, an AI agent, like Claude code or gemini would run the task prompt along with their specified characteristics, then they deisgn and plan the project steps to be sent to different "doer" agents. 

	- Software developer: Similar to the Principal engineers, but they write specific codes for a specific part of the project. These developers are the main agents for doing the development and they call sub-agents. 

	- There are several deifferent agents for peroforming different tasks: developing querys, developing fron-ent, developing backend, ....

	- Designers: Agents for front-endand any other task needs desigining. 

- Cyber security: monitors best practices for cyber security. 

- Testers: These are extremely important. The work directly under the project manager and develop different tests to make sure that the software is working exactly as intended. 


- Lead Data scientist: Similar to software engineering, but for data science: Designing different steps for accomplishing tasks data science task.  The main task of lead data scientists and engineers is communicating with the project manager and Deos on one hand and their reporters on the other hand.

	- Data scietists: Performing tasks related to data science.

- Lead Data Enigners: managing different data engineers for performing alls sorts of tasks for the project. 

	- Data enigneers: Actually doing the data engineering jobs. 

	- Sub-agents for perfomring tasks: this involves running queries in BigQuery using the command line with Claude Code.

- Busines Manager: Working with the project manager, but their goal is specifically analyzing the tasks that should be done regarding the business part of the project. 

	- Business analyst: Doing the tasks assigned by the business manger. This could include news analyzer for that specific project. 
	- Several sub-agents are needed for performing business aspects. 




# Methodology and Secretas

## Setup

All the servers are deployed in Hartwell, all in local. 
There are 4 different  images that are running:
- n8n or KingAPI using padentic AI.
- Rocket chat
- Postgres
- A module for cloudflare

The module for cloudflare is not a a full package that is dounlowded, it is a script that runs to keep the local urls available on external url. I am not paying for that. 
use login in the hartwell profile to login. 

the postgres does not need public url since it is going to interact with n8n they are both local when running. 

Use the red notebook for c*renedn*tials. 

## n8n Setup

Currently I am thinkging about migrating from n8n cause it seems so slow and hard to develop since it does not work properly with wibe coding. 



Unfurtunately, there can not be folders in the community version of n8n and hence, all the workflows are in the same folder. Instead, I separate the files by their tag. 

Here are the main and sub-tags. 

main tags:

- Fundamental (means it has a fundamental elements that could be used in other workflows)
- use_[technology] This means that this workflow uses a specific technology.  When I am typing this, we have:
	- use_pinecone
	- use_rocketChat

- agent there are the agents that can work on a problem (not created any yet)
	- reports_to_[another agent]
~~


## KingAPI:

This is the main backend of the AI assistant code. KingAPI is the home of Deos, where all the agents laying under this umbrella.


### Hirarchy of agents


I am thinking of this:

Does
- King Agents
	- Main agent
	- Personal Assistant
	- Everyday life
	- Real Friends
	- Relationship Assistant
	- Health
	- Useful Friends
- Work Assistant:
	- Kingdom
		- Project Manage:
			- planner and manager and idea developers. 
			- agile  scrum masters. 
		- Software Engineer
			- Software Developer_1
			- Software Developer_2
			- ... 	
		- Lead Data Engineer
			- Data Engineer
		- Lead Data Scientist
			- Data Scientist
	- Openbook
		- Project Manage
		- Full Stack Principal Software Engineer
			- UI/UX Designer
			- Front-end devleoper
			- Software Developer_1
			- Software Developer_2
		- Lead Data Engineer
			- Data Engineer_1
			- Data Engineer_2
		- Lead Data Scientist
			- Data Scientist_1
			- Data Scientist_2			
			- Data Scientist_3
			...
	- Stock Market 
		- Project Manage
		- Lead Data Scientist
			- Data Scientist_1 (prediction)
			- Data Scientist_2 (simulation)				- Data Scientist_3 (...)
		- Software Engineer
			- Software Developer_1 (workflow)
			- Software Developer_2 (trading)
			- Software Developer_2 (safety net and managements)


## Rocket Chat Setup

Rocket.Chat would be the main chatting system between me and the whole system. The system would reside in my poersonal Mac at home, the rocket.chat sever is also on my mac, but it has a url that could be acccessed from internet. The rocket.chat server is totally personal and no external access to that except by me. 

Later on we would connect the kingdom via other messengers like Whatsapp or Telegram, but that requires extreme causious.  

There are a few elements that are required to be set up both in rocket chat and in N8N to make the smooth connection between these two. 

1. A Rocket.chat -> n8n webhook: a webhook is a an element that can listen to a url with specific setup. To make this, first we need to create a webhook in n8n. Please see the workflow: postRocketChat, it has several elements. 

Click on the webhook and do these:

- Change HTTP Mehod to Post
- copy "Path" item, don't change other stuff like authentication. We will work on them later. 

Now create an outgoig integration in rocket.chat: go to admin page of rocket.chat, there is a three-dot sign on the left side of the page: administration, click on gear icon: workspace, find: Integrations. These are incomming and outcomming connections. 

create a new connection based on the needs to post items from different channels and groups via different users to n8n.  Here are the setup:

- Event Trigger: Message Sent, 
- Name: (use a name)
- Channel: (put a channel name that already exists)
- URLs: THis is the most important one. Use the general url of the n8n and the "path" that you coppied from the previous step. 

for instance: https://svc1.peyvastegi.uk/webhook-test/12c7b832-9a50-44f7-b1f8-711d0c92478d

DO NOT USE the  POST url address, use the above svc address /webhook-test (or webhook) then use Path. 

activate the n8n webhook, put something in the channel by that user, it should be received by the webhook.  

To make the workflow actively listening to the urls, enable "inactive/active"  at the top right of the workflow. 


* Big hint: for production where we make the workflow active, we need a new set of integration with url: https://svc1.peyvastegi.uk/webhook/    not with webhook-test.


2. A n8n to rocket.chat output:

We also need a way to send messages from n8n to rocket.chat. We do it using HTTP request, further development, including **a more secure connection** is left for future. 


Here is how to setup:

- in Rocket.chat:
	- Make a new user in the rocket.chat just for connection purposes. keep the password nad user in a safe place. 

	- make an incomming integration, similar to the above outgoing integration. THis time copy the webhook url from rocket.chat, use name, set channel, and Post as (prefferably the newly created user. 


- in n8n:


	- Create a new HTTP request, method: Post, URL: the url of the rocket.chat integration incomming webhook, Authentication None (for time being). 

Very important here: send Body: ON


Body content type: JSON
Specify Body: Using Fields Below
Name text (use the standard "text", this is what rocket.chat can understand). 
value (the value of the input from n8n, for the chat use:  {{$json.chatInput}}

THat's it! type something in the chat input, and it should go the desired channel (which is set in the incomming webhook seting). 


# Development phases:

I need help for this part, but I think there are the main steps for development:

1. I guees the first step is just planning and setting up the priorities. 
2. Then we will start making the the first agent with all the components. I would say the main components are:
	- Memory: read abd write access to postgres Relational database and vector base. So, Four different things should be tested: read/write access for relational and vector database. What we save for each element is a combination of metadata, in the relational database part, and a vector part. We are going to use openAI's embeding method for creating the vectors and retriving data from it. Also, we going to have a combination of metadata and vector search for each item. 
	- A messaging mechanism: As I am speaking now, there is a system called: google Agent development Kit which is google's attempt to create a platform for creating agents. One key feature of that is called Google's A2A system, which they have tried to connect it to core developers in Linux world and other platforms. So, for having a system that agents can communicate with each other and perform tasks, that seems like an ideal tool. However, since we don't know what will happen next month, we need to be creative and prepare ourselves for communication. So we will go with two mechanisms: A mechanism in which agents write markdown files to communicate with each other, and another mechanism for A2A communication. 
	- A log system: for keeping the logs of the agents. We also need a security system that enables agent's access to other agent's log and data. 
	- A chat system and console of communication between different agents. This works like a real company or community that agents talk to each other and communicate with me. 
	- Starting making basic agents. These agents would help us developing other agents. After that, we make the different agents that I have talked in this document. 
		- A very important sub-step of this step is making tester agents for coding and developments. For each task that we have.
		- A very important aspect of this system is the world awairness. These agents read news, follow the important accounts in different social media, search deeply about different topics and add to the overal knowledge of the Deos.  There can be also agents for social presence and influencing the world. 
	- As I mentioned earlier: a security system for mamking sure that my secrets are not going beyond the my system, even the API servers for genAI models like chatgpt and claude should not have certain access to my secrets. At the end we should have a balance between using these system and keeping our safety and security. 



# Memory phases proposal:

Here is the list of items that ( already developed in the folder: brain):

stories and  tasks, as important elements of life. Perhaps following agile methodology for persuing the success in projects, but generally, every single event in life should be recorded with appropriate links. 



# How the system is expeted to work:

There are a few set of agents:

- There is Deos who manages and controls everything. 

- Agents that interact with me (interaction_agents) : These agents have connection to me directly through rocket.chat and other messaging tools. I talk to them for the sake of talking and they reply to me depending on the case, and for the sake of recieving the commands to do stuff. 

- There agents who are manager for specific tasks (manager_agents). They orchestrate tasks for their field of experties and perform that using the worker_agents. 

- There are task agents: They are experts in accomplishing certain tasks. The task are either technical, or performing searches and monitoring, or any other things that we may need. 

Basically, the way these agents work is that:  I provide commands (or they are automatically programmed to do tasks) to the interaction agents. These agents form an agents committee to find the best plan and manager_agents . They create a prompt that includes the plan, method, and steps to take. We then give it to Claude Code or other tools in the terminal, which performs the task, generates the response, and sends the results back. The committee reviews the results and makes the next decision.

