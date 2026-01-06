import os
import json
import re
import concurrent.futures
import time
from dotenv import load_dotenv
from generate import GenerateEmail
from tqdm import tqdm

load_dotenv()

DATASET_DIR = "datasets"
FILES_TO_TEST = ["mixed.jsonl", "challenge.jsonl", "adversarial.jsonl"]

# --- CONFIGURATION ---
# 7 Variations: Shorten, Lengthen, + 5 Tones
ACTIONS = ["shorten", "lengthen", "tone"]
TONE_VARIATIONS = ["Friendly", "Sympathetic", "Professional", "Diplomatic", "Witty"]

METRICS = [
    "faithfulness", 
    "completeness", 
    "robustness", 
    "url_preservation",
    "edge_case_scan"
]

# Initialize Bots
generator_bot = GenerateEmail(deployment_name=os.getenv("GENERATOR_DEPLOYMENT", "gpt-4o-mini"))
judge_bot = GenerateEmail(deployment_name=os.getenv("JUDGE_DEPLOYMENT", "gpt-4.1"))

def parse_score(response_text):
    """Extracts floating point score from AI response."""
    match = re.search(r"Score:\s*(\d+\.\d+)", response_text)
    if match:
        return float(match.group(1))
    match_int = re.search(r"Score:\s*(\d+)", response_text)
    if match_int:
        return float(match_int.group(1))
    return 0.0

def process_single_entry(entry, action, tone_type=None):
    original_text = entry.get("content", "")
    if not original_text:
        return None

    # 1. Rewrite
    rewritten_text = generator_bot.generate(action, original_text, tone_type=tone_type)
    
    # 2. Evaluate (Parallel)
    scores = {}
    explanations = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(METRICS)) as executor:
        future_map = {
            executor.submit(judge_bot.evaluate, m, original_text, rewritten_text): m 
            for m in METRICS
        }
        
        for future in concurrent.futures.as_completed(future_map):
            metric = future_map[future]
            res = future.result()
            scores[metric] = parse_score(res)
            explanations[metric] = res 

    return {
        "id": entry.get("id"),
        "original": original_text,
        "rewritten": rewritten_text,
        "scores": scores,
        "explanations": explanations
    }

def run_test_suite():
    print("🚀 Starting GLOBAL Batch Evaluation (Aggregated)")
    print(f"Metrics: {METRICS}")
    print(f"Files: {FILES_TO_TEST}")
    print("--------------------------------------------------")
    
    # Global Accumulators
    global_metrics_sum = {m: 0.0 for m in METRICS}
    global_count = 0
    all_worst_cases = []
    
    # Build Configuration List (7 Items)
    configurations = []
    for action in ACTIONS:
        if action == "tone":
            for t in TONE_VARIATIONS:
                configurations.append({"action": action, "tone": t})
        else:
            configurations.append({"action": action, "tone": None})

    # --- MASTER LOOP ---
    for config in configurations:
        current_action = config['action']
        current_tone = config['tone']
        
        label = f"{current_action.upper()}"
        if current_tone:
            label += f" ({current_tone})"
            
        print(f"\n▶️  Processing Action: {label}")

        for filename in FILES_TO_TEST:
            filepath = os.path.join(DATASET_DIR, filename)
            if not os.path.exists(filepath):
                continue
            
            # Load ALL Entries
            entries = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except: continue
            
            # Use ALL entries in the file
            entries_to_run = entries 
            
            # Run Batch (Silent Mode - No intermediate tables)
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(process_single_entry, e, current_action, current_tone) 
                    for e in entries_to_run
                ]
                
                # Progress bar for visual feedback only
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(entries_to_run), desc=f"   📂 {filename}", leave=False):
                    res = future.result()
                    if res:
                        # Add to Global Sums
                        for m in METRICS:
                            global_metrics_sum[m] += res["scores"].get(m, 0.0)
                        global_count += 1
                        
                        # Edge Case Detection
                        failed_metrics = [m for m, s in res["scores"].items() if s < 3.0]
                        if failed_metrics:
                            all_worst_cases.append({
                                "config": label,
                                "file": filename,
                                "id": res["id"],
                                "failures": failed_metrics,
                                "scores": res["scores"],
                                "explanation": res["explanations"][failed_metrics[0]]
                            })

    # --- FINAL GLOBAL REPORT ---
    print("\n\n")
    print("="*60)
    print("📊 FINAL GLOBAL AVERAGE SCORES")
    print("="*60)
    print(f"Total Emails Processed: {global_count}")
    print(f"Total Scenarios Evaluated: {global_count * 5} metrics")
    print("-" * 60)

    if global_count > 0:
        for m in METRICS:
            avg = global_metrics_sum[m] / global_count
            
            # Grade Visualizer
            if avg >= 4.8: grade = "🌟 PERFECT"
            elif avg >= 4.5: grade = "✅ EXCELLENT"
            elif avg >= 4.0: grade = "⚠️ GOOD"
            else: grade = "❌ POOR"
            
            print(f"{m.ljust(20)}: {avg:.4f} / 5.00  [{grade}]")
    else:
        print("No data processed.")

    print("="*60)
    
    # Worst Case Summary
    print(f"\n🚩 EDGE CASES FOUND: {len(all_worst_cases)}")
    if all_worst_cases:
        print("Top 3 Failures for Review:")
        for i, case in enumerate(all_worst_cases[:3], 1):
            print(f"{i}. {case['config']} | {case['file']} (ID {case['id']})")
            print(f"   Failed: {case['failures']} -> Score: {case['scores'][case['failures'][0]]}")
            print("-" * 40)

if __name__ == "__main__":
    start_time = time.time()
    run_test_suite()
    print(f"\nTotal Runtime: {time.time() - start_time:.2f} seconds")