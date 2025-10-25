import os
from dotenv import load_dotenv
from openai import OpenAI

from agent_dataset import get_agent_records


agent_records = get_agent_records()

if not agent_records:
    raise ValueError("No agent data provided. Add at least one entry to generate files.")

# Create directory for agent files
output_dir = "agent_profiles"
os.makedirs(output_dir, exist_ok=True)

# Generate markdown files
for record in agent_records:
    filename = f"{record.name}.md"
    filepath = os.path.join(output_dir, filename)

    base_rate_display = (
        f"${record.base_rate}/hour" if record.base_rate is not None else "N/A"
    )
    success_rate_display = (
        f"{record.success_rate}%" if record.success_rate is not None else "N/A"
    )
    agent_type_display = (
        f"{record.agent_type.title()} Agent" if record.agent_type else "N/A"
    )
    industry_display = record.industry.title() if record.industry else "N/A"
    availability_display = (
        record.availability.title() if record.availability else "N/A"
    )

    # Create markdown content
    md_content = f"""# Agent Profile

{record.profile_description}

## Agent Details

- **Agent Type:** {agent_type_display}
- **Industry:** {industry_display}
- **Availability:** {availability_display}
- **Base Rate:** {base_rate_display}
- **Success Rate:** {success_rate_display}

---

*Agent ID: {record.agent_id}*
"""

    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✓ Created: {filename}")

print(
    f"\n✅ Successfully created {len(agent_records)} markdown files in '{output_dir}/' directory"
)


# Initialize OpenAI client
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))
client = OpenAI()

# Your vector store ID
VECTOR_STORE_ID = "vs_68fc1b149c04819181785e5efc9c2bcd"  # Replace with your actual vector store ID

print("\n📤 Uploading files to vector store...")

# Upload each file with attributes
for record in agent_records:
    filename = f"{record.name}.md"
    filepath = os.path.join(output_dir, filename)

    try:
        # Upload file with attributes
        with open(filepath, "rb") as file_handle:
            result = client.vector_stores.files.upload_and_poll(
                vector_store_id=VECTOR_STORE_ID,
                file=file_handle,
                attributes={
                    key: value
                    for key, value in {
                        "agent_id": record.agent_id,
                        "base_rate": record.base_rate,
                        "success_rate": record.success_rate,
                        "availability": record.availability,
                        "industry": record.industry,
                        "agent_type": record.agent_type,
                    }.items()
                    if value is not None
                },
            )

        print(f"✓ Uploaded: {filename} (status: {result.status})")

    except Exception as e:
        print(f"✗ Failed to upload {filename}: {str(e)}")

print(f"\n✅ Finished uploading to vector store: {VECTOR_STORE_ID}")
