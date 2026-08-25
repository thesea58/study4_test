import os
import json
import re

def html_to_md(html):
    if not html:
        return ""
    
    # Replace common formatting tags
    text = html
    text = re.sub(r'<(?:b|strong)>', '**', text)
    text = re.sub(r'</(?:b|strong)>', '**', text)
    text = re.sub(r'<(?:i|em)>', '*', text)
    text = re.sub(r'</(?:i|em)>', '*', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</?p>', '\n\n', text)
    text = re.sub(r'</?div>', '\n', text)
    
    # Lists
    text = re.sub(r'<ul>', '\n', text)
    text = re.sub(r'</ul>', '\n', text)
    text = re.sub(r'<li>', '- ', text)
    text = re.sub(r'</li>', '\n', text)
    
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # Clean up double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def process():
    workspace = r"d:\4.TOEIC\study4"
    json_path = os.path.join(workspace, "study4_scraped_results.json")
    md_path = os.path.join(workspace, "toeic_results.md")
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        print("Please run the scraper script in your browser and download the JSON file first.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # De-duplicate data by question number
    unique_data = {}
    for q in data:
        num = q.get("number")
        if not num:
            continue
        if num not in unique_data:
            unique_data[num] = q
        else:
            # If duplicate, prefer the one with longer explanation
            if len(q.get("explanation", "")) > len(unique_data[num].get("explanation", "")):
                unique_data[num] = q
    data = list(unique_data.values())
 
    # Post-process questions to populate correctAnswer
    for q in data:
        choices = q.get("choices", [])
        status = q.get("status")
        
        # Find user's answer
        user_ans = ""
        for c in choices:
            if c.get("checked", False):
                user_ans = c.get("value", "")
                break
                
        # If status is correct, the correct answer is the checked answer
        if status == "correct":
            q["correctAnswer"] = user_ans
        # If status is wrong but correct answer is missing, let's keep it as is or try to check if any choice is correct


        
    # Group questions by Part
    parts = {}
    stats = {"correct": 0, "wrong": 0, "unanswered": 0}
    
    for q in data:
        part_name = q.get("part", "Chưa phân loại").strip()
        if not part_name:
            part_name = "Chưa phân loại"
        if part_name not in parts:
            parts[part_name] = []
        parts[part_name].append(q)
        
        status = q.get("status", "unanswered")
        if status in stats:
            stats[status] += 1
            
    # Sort parts logically: Part 1, Part 2, ...
    sorted_parts = sorted(parts.keys(), key=lambda x: x if "Part" not in x else x)
    
    md_lines = []
    md_lines.append("# KẾT QUẢ CHI TIẾT - TOEIC PRACTICE")
    md_lines.append(f"\n## Tóm tắt kết quả")
    md_lines.append(f"- **Tổng số câu**: {len(data)}")
    md_lines.append(f"- **Đúng**: {stats['correct']} ({(stats['correct']/len(data)*100):.1f}%)")
    md_lines.append(f"- **Sai**: {stats['wrong']} ({(stats['wrong']/len(data)*100):.1f}%)")
    md_lines.append(f"- **Chưa làm**: {stats['unanswered']} ({(stats['unanswered']/len(data)*100):.1f}%)")
    
    # Section of mistakes to review
    md_lines.append("\n## ❌ DANH SÁCH CÂU SAI CẦN ÔN TẬP")
    wrong_questions = [q for q in data if q.get("status") == "wrong"]
    if wrong_questions:
        md_lines.append("Hãy tập trung sửa đổi và ôn tập lại các câu sau đây:")
        for q in sorted(wrong_questions, key=lambda x: int(x['number']) if x['number'].isdigit() else 999):
            md_lines.append(f"- [Câu {q['number']}](#câu-{q['number']}) ({q.get('part', 'N/A')})")
    else:
        md_lines.append("Tuyệt vời! Bạn không sai câu nào.")
        
    # Detailed section
    md_lines.append("\n## CHI TIẾT CÁC PHẦN THI")
    
    for part in sorted_parts:
        md_lines.append(f"\n### {part}")
        
        # Sort questions inside part by number
        qs = parts[part]
        qs_sorted = sorted(qs, key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
        
        for q in qs_sorted:
            num = q.get("number")
            status = q.get("status")
            status_icon = "✅" if status == "correct" else ("❌" if status == "wrong" else "⚪")
            status_text = "Đúng" if status == "correct" else ("Sai" if status == "wrong" else "Chưa làm")
            
            md_lines.append(f"\n#### Câu {num} - {status_icon} ({status_text})")
            
            # Context (transcript, audio, passage, image)
            context = q.get("context", "")
            if context and context.strip():
                cleaned_context = html_to_md(context)
                if cleaned_context:
                    md_lines.append("\n**Ngữ cảnh / Đoạn văn / Audio transcript:**")
                    md_lines.append("> " + cleaned_context.replace("\n", "\n> "))
            
            # Question Text
            q_text = html_to_md(q.get("questionText", ""))
            if q_text:
                md_lines.append(f"\n**Đề bài:**\n{q_text}")
                
            # Choices
            md_lines.append("\n**Các lựa chọn:**")
            for c in q.get("choices", []):
                label_cleaned = html_to_md(c.get("label", ""))
                val = c.get("value", "")
                
                # Check status
                checked = c.get("checked", False)
                is_correct = (val == q.get("correctAnswer"))
                
                prefix = "[x]" if checked else "[ ]"
                suffix = ""
                if is_correct:
                    suffix = " 🌟 (Đáp án đúng)"
                if checked and not is_correct:
                    suffix = " ❌ (Bạn đã chọn - Sai)"
                elif checked and is_correct:
                    suffix = " (Bạn đã chọn - Đúng)"
                    
                md_lines.append(f"- {prefix} {label_cleaned}{suffix}")
                
            # Explanation
            exp = q.get("explanation", "")
            if exp and exp.strip():
                # Separate Explanation and Translation if possible
                cleaned_exp = html_to_md(exp)
                md_lines.append("\n**Giải thích chi tiết:**")
                md_lines.append(f"```\n{cleaned_exp}\n```")
                
            md_lines.append("\n---")
            
    with open(md_path, "w", encoding="utf-8") as out:
        out.write("\n".join(md_lines))
        
    print(f"\nSuccess! Structured markdown file created at {md_path}")
    print(f"You can open and view it inside your editor.")

if __name__ == "__main__":
    process()
