def format_stats_dynamic(row):
    lines = []
    exclude = {"Agent Name", "Supervisor", "Formatted Stats", "GPT Summary"}
    for field in row.index:
        if field not in exclude and pd.notnull(row[field]):
            suffix = "%" if "Rate" in field or "Utilization" in field else ""
            val = f"{round(float(row[field]), 2)}{suffix}" if isinstance(row[field], (int, float)) else str(row[field])
            lines.append(f"- {field}: {val}")
    return "\n".join(lines)

def summarize_agent(row, client):
    prompt = f"""You are writing a performance summary for support agent {row['Agent Name']}.

Here are their stats:
{row['Formatted Stats']}

Write a bullet-point summary of this performance."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def summarize_team(supervisor, stats, client):
    prompt = f"""You are a team lead reviewing metrics for Supervisor {supervisor}'s team.

Here are the team's performance stats:
{stats}

Write 3–5 bullet points summarizing overall performance."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
