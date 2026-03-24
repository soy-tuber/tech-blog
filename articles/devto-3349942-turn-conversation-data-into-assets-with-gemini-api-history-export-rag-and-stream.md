---
title: "Turn Conversation Data into Assets with Gemini API: History Export, RAG, and Streamlit"
date: 2026-03-14
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/mega-gemini-google"
devto_url: "https://dev.to/soytuber/turn-conversation-data-into-assets-with-gemini-api-history-export-rag-and-streamlit-5cab"
devto_id: 3349942
---

## Introduction: Taking Back Control of the AI "Brain"

For modern engineers, LLMs (Large Language Models) like Gemini and ChatGPT are more than mere tools; they are a "second brain." From daily coding, debugging, and architectural considerations to career advice, we entrust a massive amount of our thought processes to AI. However, we face a critical issue here: "Is this valuable dialogue data truly ours?"

When buried in browser histories and practically unsearchable, past insights cannot be utilized. Moreover, if standard features like Google Takeout fail to work as expected, our intellectual assets are at risk of disappearing. Furthermore, even if you acquire powerful hardware like the latest RTX 5090 (32GB VRAM), you cannot maximize its performance without the appropriate data and workflows.

This article is a practical guide for engineers who extensively use Gemini, covering everything from techniques to export easily scattered conversation histories, to building a knowledge base using Google Workspace, and developing applications combining local LLMs and RAG (Retrieval-Augmented Generation).

From gritty hacks to automation scripts, all code is designed to work. Use this as a reference to shift your AI utilization from "consumption" to "assetization."

## Chapter 1: Export Techniques for Gemini Conversation History

Dialogues with Gemini reflect your thoughts. Let's start by securing this data locally. However, there are some points to note here.

### Challenge: Google Takeout Export Issues

Google has a data export feature called "Google Takeout," but its behavior can be unstable regarding Gemini history. When attempting to export hundreds of chat histories, I once had a perplexing experience where the downloaded Zip file was "less than 1MB" and completely empty inside.

Particularly when using Google Workspace (enterprise accounts) or when API usage is mixed in, chat histories on the Web UI may not be archived correctly. Even if exported, they are in a complex JSON structure, which is not in a human-readable format as is.

### Solution A: JSON Formatting via Python Script (If Takeout Succeeds)

If you successfully obtain `GeminiChat.json` via Google Takeout, you need to convert it into highly readable Markdown or CSV. The following Python script parses the nested JSON structure, formats the dates and titles, and outputs them.

```python
import json
import os
import csv
from datetime import datetime

def format_timestamp(ts_str):
    """Format ISO 8601 timestamps"""
    try:
        if ts_str.endswith('Z'):
            ts_str = ts_str
        dt_object = datetime.fromisoformat(ts_str)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts_str

def process_gemini_json(json_file_path, output_dir="exported_gemini_chats"):
    """Read GeminiChat.json and output Markdown and CSV"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    all_chat_data = []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Normalize data structure (ensure it's a list)
    if isinstance(data, dict):
        data = [data]
    
    print(f"Processing {len(data)} chat entries...")

    for i, chat_entry in enumerate(data):
        title = chat_entry.get('title', f"Untitled_Chat_{i+1}")
        # Remove characters unusable in filenames
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title: safe_title = f"chat_{i+1}"
        
        created_at = format_timestamp(chat_entry.get('create_time', 'Unknown'))
        
        # Generate Markdown
        md_filename = os.path.join(output_dir, f"{safe_title}.md")
        full_text = ""
        
        with open(md_filename, 'w', encoding='utf-8') as md_f:
            md_f.write(f"# {title}\n\n")
            md_f.write(f"Date: {created_at}\n\n")
            
            conversations = chat_entry.get('conversations', [])
            if not conversations and 'content' in chat_entry:
                # Fallback for different structures
                conversations = [{"speaker": "AI", "text": chat_entry.get('content')}]

            for convo in conversations:
                speaker = convo.get('speaker', 'Unknown')
                text = convo.get('text', '')
                md_f.write(f"## {speaker}\n{text}\n\n")
                full_text += f"{speaker}: {text}\n"
        
        all_chat_data.append({
            'title': title,
            'created_at': created_at,
            'summary': full_text.replace('\n', ' ')[:100] + '...',
            'file': md_filename
        })

    # CSV Output
    csv_file = os.path.join(output_dir, "summary.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'created_at', 'summary', 'file'])
        writer.writeheader()
        writer.writerows(all_chat_data)
    
    print(f"Done: Saved to {output_dir}.")

if __name__ == "__main__":
    # Specify the JSON file path here
    # json_path = "takeout/Gemini/GeminiChat.json" 
    # process_gemini_json(json_path)
    print("Please specify a JSON path to run")
```

### Solution B: Exporting via Chrome Extension (If Takeout Fails)

If Google Takeout does not work, or if the "Gemini Apps" item itself does not appear, an approach to directly save the information displayed in the browser is effective. By using Chrome extensions such as "ChatExporter for Gemini," you can extract text directly from the DOM and save it in Markdown format.

This method does not rely on server-side issues and can reliably save what is currently visible, making it highly effective as a backup. Even if there is a massive amount of history, it is crucial to select a tool that sequentially retrieves data in conjunction with browser scrolling.

## Chapter 2: Building a Knowledge Base in the Google Ecosystem (GAS × AppSheet)

It would be a waste to leave the exported data as is. Next, we will rebuild this as a searchable "knowledge base" within Google Workspace. By combining Google Apps Script (GAS) and AppSheet, you can create a secure AI assistant that requires no server management.

### Advantages of a Loosely Coupled Architecture

By keeping "Google Sheets (database)," "GAS (logic)," and "AppSheet (UI)" loosely coupled, this system achieves high maintainability.

- Google Sheets: Saves conversation logs as structured data. Becomes the search target for RAG.
- GAS: Calls the Gemini API and reads/writes to the sheet.
- AppSheet: Provides an intuitive UI accessible from smartphones and PCs.

### Implementation: GAS Code to Auto-Save Gemini History

The following code is a GAS function that receives a request from AppSheet, calls the API of the latest inference model, Gemini 3.1 Pro, generates an answer, and appends the result to a spreadsheet.

```javascript
const GEMINI_API_KEY = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
const SHEET_ID = 'YOUR_SPREADSHEET_ID';

function callGemini(prompt, historyContext) {
  // Use Gemini 3.1 Pro Preview
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key=${GEMINI_API_KEY}`;
  
  // Append past context to prompt if available (Simple RAG)
  const finalPrompt = historyContext 
    ? `Please answer based on the following past context.\nContext: ${historyContext}\n\nQuestion: ${prompt}`
    : prompt;

  const payload = {
    "contents": [
      {
        "parts": [{"text": finalPrompt}]
      }
    ]
  };

  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const json = JSON.parse(response.getContentText());
    if (json.candidates && json.candidates[0].content) {
      return json.candidates[0].content.parts[0].text;
    } else {
      return "Error: Could not generate a response.";
    }
  } catch (e) {
    return `Communication Error: ${e.toString()}`;
  }
}

// Function executed via Webhook or Trigger from AppSheet
function onUserQuery(e) {
  // * In reality, assumes receiving arguments from AppSheet Automation, etc.
  const userPrompt = e ? e.prompt : "Test Question"; 
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Log');
  
  // Logic to search related information from past logs (Simplified)
  const lastRow = sheet.getLastRow();
  let context = "";
  if (lastRow > 1) {
    context = sheet.getRange(lastRow, 3).getValue(); // Use previous answer as context
  }

  const aiResponse = callGemini(userPrompt, context);
  
  // Save timestamp, prompt, and response
  sheet.appendRow([new Date(), userPrompt, aiResponse]);
  
  return aiResponse;
}
```

This script works by creating it as a GAS project from Google Sheets extensions and setting the API key in script properties. This allows all your conversations to accumulate in a spreadsheet, making it a searchable database.

## Chapter 3: Automated Slide Generation with RTX 5090 and RAG

Once the knowledge base is ready, the next step is output automation. Here, we leverage the power of the latest high-end GPU "RTX 5090" to achieve content generation specialized in professional fields like law and technology, and automated output to Google Slides.

### Local LLM Utilizing RTX 5090 (32GB VRAM)

The most significant feature of the RTX 5090 is its vast 32GB VRAM capacity and high inference performance thanks to the Blackwell architecture. This allows loading mid-to-large-scale LLMs like Gemma 3 (27B) and Qwen2.5-32B fully with minor quantization.

In specialized tasks involving complex logical puzzles, hallucinations tend to occur with general API-based models. Thus, it is effective to use a library called Unsloth to fine-tune a local LLM on the RTX 5090.

```python
from unsloth import FastLanguageModel
import torch

def train_local_model():
    # Load model leveraging RTX 5090's 32GB VRAM
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/gemma-3-27b-it", # Use Gemma 3 27B model
        max_seq_length = 4096,
        dtype = None, # Auto setup
        load_in_4bit = True, # 4-bit quantization to run 27B model comfortably
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
    )
    
    # Dataset loading and Trainer configuration go here
    print("Training started: RTX 5090 VRAM 32GB Environment")
```

### Automatic Conversion from Content to Slides

Highly accurate answers and explanations generated by local LLMs or the Gemini API are output structured in JSON format. This is read by Google Apps Script to automatically generate slides.

```javascript
function generateSlidesFromData() {
  // Slide data to generate (Assuming received in JSON from Python)
  const slidesData = [
    {
      title: "Results",
      body: "Achieved accuracy comparable to Gemini 3.1 Pro in specialized interpretation.",
      points: ["Faster inference", "Lower cost"]
    }
  ];

  const presentation = SlidesApp.create("AI Generated Report_RTX5090 Verification");
  const slides = presentation.getSlides();
  if (slides.length > 0) slides[0].remove();

  slidesData.forEach(data => {
    const slide = presentation.appendSlide(SlidesApp.PredefinedLayout.TITLE_AND_BODY);
    
    const titleShape = slide.getShapes().find(s => s.getPlaceholderType() === SlidesApp.PlaceholderType.TITLE);
    if (titleShape) titleShape.getText().setText(data.title);
    
    const bodyShape = slide.getShapes().find(s => s.getPlaceholderType() === SlidesApp.PlaceholderType.BODY);
    if (bodyShape) {
      let textContent = data.body + "\n\n";
      data.points.forEach(p => textContent += `- ${p}\n`);
      bodyShape.getText().setText(textContent);
    }
  });

  Logger.log("Slide generation complete: " + presentation.getUrl());
}
```

This automation significantly reduces document creation time. Humans can focus on structure and content review, freed from the simple task of layout adjustments.

## Chapter 4: Real-time Dashboard Construction (Streamlit + Gemini)

Lastly, we'll build a real-time dashboard useful for daily data analysis and monitoring. With the Python framework "Streamlit", you can create web apps in a few lines of code without HTML or CSS knowledge. By integrating the Gemini API, a dashboard where AI interprets data meanings in real-time is completed.

### Implementing the Streamlit Application

The following code takes user input, performs sentiment analysis using Gemini 2.0 Flash (characterized by fast responses), and graphs the results in real-time.

```python
import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import altair as alt
import json

# Set API Key (Recommended to read from environment variables)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("API key is not set.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
# Use a fast model suitable for real-time processing
model = genai.GenerativeModel('gemini-2.0-flash')

def main():
    st.set_page_config(layout="wide", page_title="Gemini AI Dashboard")
    st.title("Gemini Real-time Analysis Dashboard")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar: Display history
    with st.sidebar:
        st.header("Analysis History")
        for msg in reversed(st.session_state.messages):
            st.text(f"{msg['role']}: {msg['content'][:20]}...")

    # Main Area: Input and Display
    user_input = st.text_input("Enter text to analyze:")

    if st.button("Start Analysis") and user_input:
        st.session_state.messages.append({"role": "User", "content": user_input})
        
        with st.spinner("Gemini is thinking..."):
            try:
                # Prompt forcing JSON output
                prompt = f"""
                Perform sentiment analysis on the following text and output the percentages of positive, negative, and neutral in JSON format.
                Set the key to 'sentiment' and return a list format with {{"category": "...", "percentage": ...}}.
                Text: {user_input}
                """
                response = model.generate_content(prompt)
                response_text = response.text
                
                # Extract JSON part (Simple processing)
                json_str = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(json_str)
                
                # Draw graph
                if "sentiment" in data:
                    df = pd.DataFrame(data["sentiment"])
                    chart = alt.Chart(df).mark_arc().encode(
                        theta=alt.Theta(field="percentage", type="quantitative"),
                        color=alt.Color(field="category", type="nominal"),
                        tooltip=['category', 'percentage']
                    ).properties(title="Sentiment Analysis Results")
                    
                    st.altair_chart(chart, use_container_width=True)
                    st.success("Analysis Complete")
                    
                    st.session_state.messages.append({"role": "AI", "content": str(data)})
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
```

This dashboard can be applied to various uses, such as analyzing customer feedback or detecting the mood in internal chats. Gemini's fast response and Streamlit's convenience accelerate prototyping speeds.

## Conclusion: Building a Co-creative Relationship with AI

In this article, we introduced four phases to utilize the Gemini API.

- **Storage:** Reliably export dialogue data using Chrome extensions or scripts.
- **Management:** Build your own knowledge base using GAS and Google Sheets.
- **Generation:** Leverage the power of RTX 5090 (32GB) to generate content via local LLMs and document it via GAS.
- **Visualization:** Analyze data in real-time with Streamlit to support decision-making.

These technologies show their true value when combined rather than used alone. A powerful hardware environment like the RTX 5090 serves as a foundation for freely manipulating AI locally.

Start by exporting your history. Within it, you should find useful insights that trace your own thought processes.
