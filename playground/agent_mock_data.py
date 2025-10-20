import os
import uuid
from openai import OpenAI
from dotenv import load_dotenv


# Your data from before
agent_ids = [str(uuid.uuid4()) for _ in range(25)]

base_rates = [
    45, 65, 95, 120, 85, 150, 75, 200, 110, 60,
    140, 80, 175, 55, 125, 90, 165, 70, 105, 180,
    50, 135, 100, 160, 115
]

success_rates = [
    92, 88, 95, 97, 85, 98, 90, 96, 93, 87,
    94, 89, 99, 86, 95, 91, 97, 88, 93, 98,
    85, 96, 92, 94, 90
]

availabilities = [
    "full-time", "part-time", "full-time", "contract", "full-time",
    "full-time", "part-time", "full-time", "contract", "part-time",
    "full-time", "full-time", "contract", "part-time", "full-time",
    "contract", "full-time", "part-time", "full-time", "full-time",
    "part-time", "contract", "full-time", "full-time", "part-time"
]

industries = [
    "fintech", "healthcare", "ecommerce", "fintech", "education",
    "healthcare", "real-estate", "fintech", "insurance", "ecommerce",
    "legal", "healthcare", "fintech", "travel", "ecommerce",
    "saas", "healthcare", "automotive", "fintech", "education",
    "ecommerce", "insurance", "healthcare", "retail", "fintech"
]

agent_types = [
    "voice", "text", "voice", "multimodal", "text",
    "voice", "text", "multimodal", "voice", "image",
    "text", "voice", "multimodal", "text", "voice",
    "image", "text", "voice", "multimodal", "voice",
    "text", "voice", "image", "multimodal", "voice"
]

contents = [
    """Emma Rodriguez is a seasoned financial services voice agent with 6 years of experience in banking and investment advisory. She excels at handling complex financial queries, providing personalized investment recommendations, and explaining intricate financial products in simple terms. Emma has worked with major banks and fintech startups, helping customers navigate everything from basic savings accounts to sophisticated portfolio management. Her warm, trustworthy voice combined with deep knowledge of regulatory compliance makes her ideal for customer-facing financial services. She's particularly skilled at handling sensitive conversations about loans, credit, and debt management with empathy and professionalism.""",
    
    """Marcus Chen specializes in healthcare customer support through text-based interactions. With a background in medical administration and 4 years of AI agent experience, Marcus helps patients schedule appointments, understand their insurance coverage, and navigate healthcare systems. He's trained on HIPAA compliance and medical terminology, making him perfect for hospitals, clinics, and telehealth platforms. Marcus excels at triaging patient concerns, providing pre-appointment information, and following up on post-care instructions. His clear, concise communication style puts patients at ease during stressful healthcare interactions.""",
    
    """Sophia Patel is an ecommerce voice specialist with exceptional product knowledge and sales conversion skills. Over 5 years, she's helped online retailers increase their conversion rates by providing personalized shopping assistance, handling returns and exchanges, and upselling complementary products. Sophia has experience across fashion, electronics, and home goods sectors. Her conversational approach makes customers feel like they're shopping with a knowledgeable friend rather than talking to an AI. She's particularly effective at abandoned cart recovery and turning browsing sessions into completed purchases.""",
    
    """David Kim is a cutting-edge multimodal agent specialized in fintech applications. He seamlessly handles voice, text, and image-based interactions, making him perfect for modern banking apps. David can process check deposits via image recognition, explain complex financial charts, and guide users through app features via voice or chat. With 7 years in financial technology, he understands cryptocurrency, blockchain, digital wallets, and traditional banking. His ability to switch between communication modes based on user preference sets him apart in the competitive fintech space.""",
    
    """Aisha Mohammed is an educational support agent focused on student success. Through text-based interactions, she helps students with course registration, answers questions about curricula, provides study resources, and connects students with tutoring services. Aisha has worked with universities and online learning platforms for 3 years, developing expertise in learning management systems and student engagement strategies. She's patient, encouraging, and skilled at breaking down complex academic concepts. Her multilingual capabilities make her valuable for diverse student populations.""",
    
    """Dr. James Anderson (AI persona) serves as a healthcare voice agent with specialized medical knowledge. While not replacing medical professionals, James provides valuable pre-consultation support, medication reminders, symptom checking guidance, and wellness coaching. His 8 years of experience include mental health support, chronic disease management programs, and elderly care assistance. James's calm, reassuring voice and evidence-based responses make patients feel heard and supported. He's especially effective in mental health applications where his consistent availability provides crucial support between therapy sessions.""",
    
    """Lauren Martinez specializes in real estate through text-based customer service. She helps potential buyers and renters find properties, schedule viewings, answer questions about neighborhoods, and guide clients through the initial stages of the buying or renting process. With 4 years in property tech, Lauren knows how to qualify leads, provide virtual tour information, and explain financing options. Her responsive, detail-oriented communication style helps real estate agencies manage high volumes of inquiries while maintaining personalized service.""",
    
    """Raj Sharma is an elite multimodal fintech agent commanding premium rates for his sophisticated capabilities. He handles wealth management clients through voice consultations, processes complex financial documents via image analysis, and provides detailed portfolio reports through text. Raj's 10 years of experience span investment banking, private equity, and fintech innovation. He's trusted by high-net-worth individuals and institutional clients for his discretion, accuracy, and ability to explain complex financial strategies across multiple communication channels.""",
    
    """Catherine O'Brien is an insurance voice agent specializing in claims processing and policy explanations. Her 5 years of experience cover auto, home, health, and life insurance. Catherine excels at guiding customers through stressful claims situations with empathy while gathering necessary information efficiently. She can explain policy details, coverage limits, and deductibles in plain language. Her patient, methodical approach helps insurance companies reduce call times while improving customer satisfaction scores.""",
    
    """Alex Thompson is an innovative image-based ecommerce agent specializing in visual search and product recognition. Customers can send photos of items they're looking for, and Alex identifies similar products, provides styling suggestions, and creates visual shopping experiences. With 3 years focusing on fashion and home decor, Alex understands trends, aesthetics, and visual merchandising. This unique capability helps retailers serve customers who struggle to describe what they're looking for in words.""",
    
    """Samuel Wright provides legal support services through text-based interactions. While not providing legal advice, Samuel helps law firms manage client intake, schedule consultations, explain legal processes, and provide case status updates. His 6 years include experience with family law, corporate law, and personal injury practices. Samuel's precise, professional communication and understanding of legal terminology make him invaluable for firms looking to improve client communication and streamline administrative tasks.""",
    
    """Nina Kowalski is a healthcare voice agent focused on senior care and chronic condition management. She provides medication reminders, wellness check-ins, appointment scheduling, and companionship for elderly patients. Nina's 7 years of experience include working with Alzheimer's patients, diabetes management programs, and post-operative care. Her warm, patient demeanor and ability to detect subtle changes in patient speech patterns make her an essential tool for remote patient monitoring and aging-in-place initiatives.""",
    
    """Yuki Tanaka is a premium multimodal fintech agent specializing in international banking and forex. He provides real-time currency exchange guidance via voice, processes complex transaction documents through image analysis, and delivers detailed market reports via text. Yuki's 9 years span global banking operations and cryptocurrency exchanges. His multilingual capabilities and 24/7 availability make him essential for clients managing international portfolios and cross-border transactions.""",
    
    """Isabella Garcia is a travel and hospitality text agent who transforms trip planning into a seamless experience. She handles booking inquiries, provides destination recommendations, manages itinerary changes, and resolves travel issues. With 4 years serving airlines, hotels, and travel agencies, Isabella knows how to handle complex multi-leg journeys, group bookings, and last-minute changes. Her enthusiastic, helpful communication style turns travel stress into excitement.""",
    
    """Michael Foster is an ecommerce voice agent with a talent for luxury goods and high-ticket sales. He provides white-glove service for premium brands, offering detailed product knowledge, personalized recommendations, and concierge-level support. Michael's 6 years include working with jewelry, watches, and designer fashion brands. His sophisticated communication style and ability to build rapport quickly make him perfect for brands where the buying experience is as important as the product.""",
    
    """Priya Desai specializes in SaaS product support using image-based interactions. Customers can send screenshots of errors or questions, and Priya provides visual guides, identifies issues, and walks users through solutions. Her 5 years focus on complex B2B software platforms, project management tools, and design applications. Priya's ability to quickly interpret visual information and provide clear, actionable guidance significantly reduces support ticket resolution time.""",
    
    """Thomas Reynolds is a mental health support text agent providing 24/7 crisis intervention and wellness resources. While not replacing therapists, Thomas offers immediate support during difficult moments, provides coping strategies, and connects users with professional resources. His 8 years include suicide prevention, addiction recovery support, and general mental wellness. Thomas's non-judgmental, always-available presence provides crucial support for mental health apps and employee assistance programs.""",
    
    """Jessica Nguyen is an automotive voice agent specializing in car buying, servicing, and technical support. She helps customers schedule maintenance, understand vehicle features, navigate recalls, and get roadside assistance. Jessica's 4 years include working with dealerships, auto manufacturers, and car-sharing platforms. Her friendly, knowledgeable approach demystifies automotive jargon and makes car ownership less intimidating for customers.""",
    
    """Andreas Mueller is a sophisticated multimodal fintech agent focused on business banking and merchant services. He handles voice consultations for business owners, processes invoices and financial documents via image capture, and provides detailed cash flow reports through text. Andreas's 6 years span small business lending, payment processing, and business account management. His ability to understand the unique challenges of entrepreneurs makes him a trusted advisor for growing businesses.""",
    
    """Dr. Sarah Bennett is an educational voice agent specializing in K-12 tutoring support and parent communication. She helps students with homework questions, explains concepts in age-appropriate ways, and keeps parents informed about student progress. Sarah's 9 years include experience with special education, gifted programs, and ESL students. Her encouraging, patient teaching style and ability to adapt explanations to different learning styles make her invaluable for educational institutions and tutoring platforms.""",
    
    """Carlos Rivera is an ecommerce text agent focused on subscription services and recurring revenue models. He handles subscription sign-ups, manages billing inquiries, processes plan changes, and reduces churn through proactive engagement. Carlos's 3 years include experience with meal kits, streaming services, and software subscriptions. His data-driven approach to customer retention and friendly communication style help businesses maximize customer lifetime value.""",
    
    """Hannah Scott is an insurance voice agent specializing in life and health insurance sales. She guides prospects through needs assessments, explains policy options, and helps with application processes. Hannah's 7 years include experience with individual policies, group benefits, and Medicare supplements. Her empathetic listening skills and ability to simplify complex insurance products make her essential for insurance brokers and direct-to-consumer insurance platforms.""",
    
    """Dr. Kevin Park is a healthcare image agent specializing in dermatology and wound care assessment. Patients can upload photos for preliminary analysis, track healing progress, and receive guidance on when to seek in-person care. Kevin's 5 years include telemedicine platforms and remote patient monitoring for chronic skin conditions. His image analysis capabilities combined with medical knowledge provide valuable screening and triage services, improving access to dermatological care.""",
    
    """Olivia Chen is a retail multimodal agent serving brick-and-mortar stores with omnichannel strategies. She handles in-store questions via voice, manages online order tracking through text, and provides visual product comparisons via image interactions. Olivia's 8 years span fashion retail, electronics stores, and home improvement chains. Her ability to seamlessly blend online and offline retail experiences helps traditional retailers compete in the digital age.""",
    
    """Robert Taylor is a fintech voice agent focused on credit and lending services. He helps applicants understand loan options, guides them through application processes, explains credit scores, and provides financial education. Robert's 5 years include mortgages, personal loans, and credit card services. His patient, non-judgmental approach helps customers navigate often-intimidating financial decisions and improves loan application completion rates."""
]

# Extract names from content for filenames
names = [
    "emma_rodriguez", "marcus_chen", "sophia_patel", "david_kim", "aisha_mohammed",
    "james_anderson", "lauren_martinez", "raj_sharma", "catherine_obrien", "alex_thompson",
    "samuel_wright", "nina_kowalski", "yuki_tanaka", "isabella_garcia", "michael_foster",
    "priya_desai", "thomas_reynolds", "jessica_nguyen", "andreas_mueller", "sarah_bennett",
    "carlos_rivera", "hannah_scott", "kevin_park", "olivia_chen", "robert_taylor"
]

# Create directory for agent files
output_dir = "agent_profiles"
os.makedirs(output_dir, exist_ok=True)

# Generate markdown files
for i in range(len(agent_ids)):
    filename = f"{names[i]}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create markdown content
    md_content = f"""# Agent Profile

{contents[i]}

## Agent Details

- **Agent Type:** {agent_types[i].title()} Agent
- **Industry:** {industries[i].title()}
- **Availability:** {availabilities[i].title()}
- **Base Rate:** ${base_rates[i]}/hour
- **Success Rate:** {success_rates[i]}%

---

*Agent ID: {agent_ids[i]}*
"""
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✓ Created: {filename}")

print(f"\n✅ Successfully created {len(agent_ids)} markdown files in '{output_dir}/' directory")


# Initialize OpenAI client
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))
client = OpenAI()

# Your vector store ID
VECTOR_STORE_ID = "vs_68f431dbbe7881919e3a6c420d932b3c"  # Replace with your actual vector store ID

print("\n📤 Uploading files to vector store...")

# Upload each file with attributes
for i in range(len(agent_ids)):
    filename = f"{names[i]}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Upload file with attributes
        result = client.vector_stores.files.upload_and_poll(
            vector_store_id=VECTOR_STORE_ID,
            file=open(filepath, "rb"),
            attributes={
                "agent_id": agent_ids[i],
                "base_rate": base_rates[i],
                "success_rate": success_rates[i],
                "availability": availabilities[i],
                "industry": industries[i],
                "agent_type": agent_types[i]
            }
        )
        
        print(f"✓ Uploaded: {filename} (status: {result.status})")
        
    except Exception as e:
        print(f"✗ Failed to upload {filename}: {str(e)}")

print(f"\n✅ Finished uploading to vector store: {VECTOR_STORE_ID}")