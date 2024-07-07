from ollama import Client

post = """
SECURITYWEEK NETWORK:
Cybersecurity News
Webcasts
Virtual Events
ICS Cybersecurity Conference
Malware & Threats
Security Operations
Security Architecture
Risk Management
CISO Strategy
ICS/OT
Funding/M&A
Cybersecurity News
Webcasts
Virtual Events
ICS Cybersecurity Conference
CONNECT WITH US
 
 

Hi, what are you looking for?

Malware & Threats
Cyberwarfare
Cybercrime
Data Breaches
Fraud & Identity Theft
Nation-State
Ransomware
Vulnerabilities
Security Operations
Threat Intelligence
Incident Response
Tracking & Law Enforcement
Security Architecture
Application Security
Cloud Security
Endpoint Security
Identity & Access
IoT Security
Mobile & Wireless
Network Security
Risk Management
Cyber Insurance
Data Protection
Privacy & Compliance
Supply Chain Security
CISO Strategy
Cyber Insurance
CISO Conversations
CISO Forum
ICS/OT
Industrial Cybersecurity
ICS Cybersecurity Conference
Funding/M&A
Cybersecurity Funding
M&A Tracker
DATA BREACHES
Some Data Is ‘Breached’ During a Hacking Attack on the Alabama Education Department

Alabama’s education superintendent said some data was breached during a hacking attempt at the State Department of Education.

By

Associated Press


July 5, 2024

Flipboard

Reddit

Whatsapp

Email

Alabama’s education superintendent said Wednesday that some data was “breached” during a hacking attempt at the Alabama State Department of Education.

Superintendent Eric Mackey said the June 17 attack was stopped while it was in progress. He said they are working to determine exactly what information might have been compromised.

Mackey said “there is a possibility” that some student and employee data might have been compromised in the attack and urged people to monitor their credit.

“What I would say is to all parents and all local and state education employees out there, they should monitor their credit. They should assume that there is a possibility that some of their data was compromised,” Mackey said at a Wednesday press conference.

He said they have brought in a contractor to go “line by line” through state servers to determine what information may have been taken by the hackers. He added that employee bank account and direct deposit information is not at risk because they don’t keep that information on state servers.

“We don’t know exactly what data was breached and we can’t disclose everything. But again, the attack on our system was interrupted and stopped by our IT professionals before the hackers could access everything they were after. That we know,” Mackey said.

Mackey said they believed the hackers were attempting to encrypt data and extort a ransom for its release. He said there is an ongoing federal criminal investigation into the attack since they believed it involved foreign hackers.

The Department of Education created a website https://www.alabamaachieves.org/databreach/ to provide information about the hacking attempt and an email, databreach@alsde.edu, for people to submit questions.

ADVERTISEMENT. SCROLL TO CONTINUE READING.

Related: K-12 Schools Improve Protection Against Online Attacks, but Many Are Vulnerable to Ransomware Gangs

Related: Android Devices With Backdoored Firmware Found in US Schools

Related: 55,000 Impacted by Cyberattack on California School Association 

WRITTEN BY
Associated Press

More from Associated Press
Brazil Data Regulator Bans Meta From Mining Data to Train AI Models
WikiLeaks Founder Julian Assange Returns to Australia a Free Man After US Legal Battle Ends
The EU Targets Russia’s LNG Ghost Fleet With Sanctions as Concern Mounts About Hybrid Attacks
Indonesia Says a Cyberattack Has Compromised Its Data Center but It Won’t Pay the $8 Million Ransom
Car Dealerships in North America Revert to Pens and Paper After Cyberattacks on Software Provider
WikiLeaks Founder Julian Assange Will Plead Guilty in Deal With US and Return to Australia
Chinese Hackers Have Stepped Up Attacks on Taiwanese Organizations, Cybersecurity Firm Says
Japan’s Space Agency Was Hit by Multiple Cyberattacks, but Officials Say No Sensitive Data Was Taken
Latest News
Russian-Linked Cybercampaigns put a Bull’s-Eye on France. Their Focus? The Olympics and Elections
Hacker Stole Secrets From OpenAI
How Intelligence Sharing Can Help Keep Major Worldwide Sporting Events on Track
In Other News: Microsoft Details ICS Flaws, Smart Grill Hacking, Predator Spyware Activity
OVHcloud Sees Record 840 Mpps DDoS Attack
California Advances Unique Safety Regulations for AI Companies Despite Tech Firm opposition
Twilio Confirms Data Breach After Hackers Leak 33M Authy User Phone Numbers
Europol Announces Crackdown on Cobalt Strike Servers Used by Cybercriminals
TRENDING
Daily Briefing Newsletter

Subscribe to the SecurityWeek Email Briefing to stay informed on the latest threats, trends, and technology, along with insightful columns from industry experts.

 
CIEM Chat: How to Reduce Cloud Identity Risk

Join the session as we discuss the challenges and best practices for cybersecurity leaders managing cloud identities.

Register
Event: AI Risk Summit | Ritz-Carlton, Half Moon Bay, CA

The AI Risk Summit brings together security and risk management executives, AI researchers, policy makers, software developers and influential business and government stakeholders.

Register
PEOPLE ON THE MOVE

Managed security platform Deepwatch has named John DiLullo as Chief Executive Officer.

Technology company Tools for Humanity (TFH) hires Damien Kieran as CPO and Adrian Ludwig as CISO.

AI driven XDR provider Vectra AI has appointed Sailesh Munagala as Chief Financial Officer.

More People On The Move
EXPERT INSIGHTS
How Intelligence Sharing Can Help Keep Major Worldwide Sporting Events on Track

The Olympic Games is only 29 days long, so set up and take down is a very intense period, where the threat actors can take advantage. (Marc Solomon)

From the SOC to Everyday Success: Data-Driven Life Lessons from a Security Analyst

By taking a data-driven approach to life, grounded in truth and facts, we can improve our chances of making better decisions and achieving better results. (Joshua Goldfarb)

The Perilous Role of the CISO: Navigating Modern Minefields

As organizations grapple with the implications of cybersecurity on their bottom line and reputation, the question of whether the CISO role is worth the inherent risks looms large. (Jennifer Leggio)

Know Your Adversary: Why Tuning Intelligence-Gathering to Your Sector Pays Dividends

Without tuning your approach to fit your sector, amongst other variables, you’ll be faced with an unmanageable amount of noise. (Marc Solomon)

When Vendors Overstep – Identifying the AI You Don’t Need

AI models are nothing without vast data sets to train them and vendors will be increasingly tempted to harvest as much data as they can and answer any questions later. (Alastair Paterson)

Flipboard

Reddit

Whatsapp

Email

Popular Topics
Cybersecurity News
Industrial Cybersecurity
Security Community
Virtual Cybersecurity Events
Webcast Library
CISO Forum
AI Risk Summit
ICS Cybersecurity Conference
Cybersecurity Newsletters
Stay Intouch
Cyber Weapon Discussion Group
RSS Feed
Security Intelligence Group
Follow SecurityWeek on LinkedIn
About SecurityWeek
Advertising
Event Sponsorships
Writing Opportunities
Feedback/Contact Us
News Tips

Got a confidential news tip? We want to hear from you.

Submit Tip
Advertising

Reach a large audience of enterprise cybersecurity professionals

Contact Us
Daily Briefing Newsletter

Subscribe to the SecurityWeek Daily Briefing and get the latest content delivered to your inbox.

 
Privacy Policy

Copyright © 2024 SecurityWeek ®, a Wired Business Media Publication. All Rights Reserved.
"""
template = """
Summarize cybersecurity blog posts and news articles concisely and informatively. Follow these guidelines:

Important: Start your summary immediately without restating or interpreting the query.
Structure:

One-sentence overview
3-5 key bullet points
Brief conclusion/implications


Include:

Specific threats, vulnerabilities, or attacks
Affected systems or organizations
Simplified technical details
Recommended actions
Potential impacts


Style:

Clear, concise language for all readers
Neutral tone
Define complex terms briefly


Length: 150-250 words
Additional:

Include relevant dates
Highlight expert quotes
Provide context if part of ongoing story
Avoid personal opinions



Format:
[Overview]
Key Points:

[Point 1]
[Point 2]
[Point 3]

[Conclusion]
Aim for clarity, accuracy, and conciseness in your summaries. Do not preface your summary with any statements about the query or article content.
"""
client = Client(host="10.0.10.9:11435")
model="gemma2"
keep_alive = 60
output = client.generate(model=model, prompt=post, system=template, keep_alive=keep_alive)

print(output["response"])