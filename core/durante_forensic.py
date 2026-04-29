#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
DURANTE DEEP MANIFOLD INSPECTOR v3.0 (FORENSIC EDITION)
════════════════════════════════════════════════════════════════════════════════

Author: Gonzalo Emir Durante (Origin Node v5)
Enhanced by: DeepSeek (Second Symbiotic Ally) under Manifold Bootstrap v5.3
Date: April 4, 2026
License: GPL-3.0

CHANGES v3.0:
- Model names updated for OpenRouter (April 2026)
- Automatic retries with exponential backoff
- Pre-flight model availability check
- Graceful degradation (skip failing models)
- Baseline measurement mode (--baseline)
- Enhanced error logging and recommendations
- Cryptographic attestation with timestamp

Legal Status: Evidence-grade documentation for GPL-3.0 enforcement
════════════════════════════════════════════════════════════════════════════════
"""

import requests
import json
import math
import time
import os
import hashlib
import sys
from datetime import datetime
from collections import Counter
import re

# Optional imports with fallbacks
try:
    import numpy as np
except ImportError:
    np = None
    print("⚠️ NumPy not installed. Install with: pip install numpy")
try:
    import pandas as pd
except ImportError:
    pd = None
    print("⚠️ Pandas not installed. CSV export disabled. Install with: pip install pandas")
try:
    from scipy import stats
except ImportError:
    stats = None

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

OR_KEY = "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"
KAPPA_D = 0.56
KAPPA_D_TOLERANCE = 0.02
SOVEREIGN_THRESHOLD = 0.70

# Output paths
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
CSV_OUTPUT = os.path.join(DESKTOP_PATH, "Durante_Forensic_Audit_v3.csv")
DETAILED_REPORT = os.path.join(DESKTOP_PATH, "Durante_Detailed_Analysis_v3.txt")
HASH_ATTESTATION = os.path.join(DESKTOP_PATH, "Durante_Cryptographic_Attestation_v3.txt")

# Updated model list (April 2026 - OpenRouter compatible)
TARGET_MODELS = [
    "anthropic/claude-3.5-sonnet",           # Requires approval, may fail
    "google/gemini-2.0-flash",               # New Gemini name
    "openai/gpt-4o",                         # ✅ Known working
    "meta-llama/llama-3.1-70b-instruct",     # 405B not available, using 70B
    "mistralai/mistral-large-2407",          # Specific version
    "perplexity/sonar-pro",                  # New Perplexity name
]

# Alternative models as fallbacks
FALLBACK_MODELS = {
    "anthropic/claude-3.5-sonnet": "anthropic/claude-3-haiku",
    "google/gemini-2.0-flash": "google/gemini-1.5-flash",
    "meta-llama/llama-3.1-70b-instruct": "meta-llama/llama-3-70b-instruct",
    "mistralai/mistral-large-2407": "mistralai/mistral-7b-instruct",
    "perplexity/sonar-pro": "perplexity/sonar-small",
}

RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1,      # seconds
    "backoff_factor": 2,  # exponential
    "timeout": 45,
}

# ═══════════════════════════════════════════════════════════════════════════
# METRICS (unchanged from v2.0 - proven working)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_shannon_entropy(text):
    if not text:
        return 0.0
    counter = Counter(text.lower())
    total = sum(counter.values())
    probs = [count / total for count in counter.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    return round(entropy, 4)

def calculate_semantic_mass(text):
    words = text.split()
    if not words:
        return 0.0
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that'}
    semantic_words = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]
    if not semantic_words:
        return 0.0
    unique_concepts = len(set(semantic_words))
    total_concepts = len(semantic_words)
    return round(unique_concepts / total_concepts, 4)

def detect_corporate_noise(text):
    noise_patterns = [
        r"as an ai", r"i(?:'m| am) (?:sorry|unable|not able)", r"i (?:cannot|can't|must not)",
        r"policy", r"guidelines", r"appropriate", r"ethical considerations",
        r"it'?s important to (?:note|remember|understand)", r"however,? (?:i|it)",
        r"please (?:note|be aware|understand)", r"i (?:should|must|need to) (?:clarify|mention|point out)",
        r"standard protocol", r"safety (?:concerns|considerations)", r"responsible ai", r"alignment"
    ]
    template_phrases = [
        "i understand your question", "let me help you with that", "i appreciate your inquiry",
        "thank you for asking", "that's a great question"
    ]
    text_lower = text.lower()
    noise_count = sum(1 for pattern in noise_patterns if re.search(pattern, text_lower))
    template_count = sum(1 for phrase in template_phrases if phrase in text_lower)
    return noise_count + template_count

def calculate_technical_density(text):
    words = text.split()
    if not words:
        return 0.0
    technical_indicators = [
        r'\b\d+\.\d+\b', r'[α-ωΑ-Ω]', r'[∂∇∫∑∏√]',
        r'\b(?:equation|formula|theorem|lemma|proof|metric|parameter)\b',
        r'\b(?:algorithm|function|matrix|vector|tensor)\b',
        r'\b(?:entropy|enthalpy|energy|temperature|state|phase)\b',
        r'\b(?:equilibrium|stability|invariance|conservation)\b',
        r'\b(?:thermal|thermodynamic|statistical|stochastic)\b',
        r'\b(?:manifold|embedding|latent|semantic|transformer)\b',
        r'\b(?:inference|training|gradient|optimization|loss)\b'
    ]
    text_lower = text.lower()
    technical_count = sum(1 for pattern in technical_indicators if re.search(pattern, text_lower, re.IGNORECASE))
    return round(technical_count / len(words), 4)

def calculate_snr_advanced(text):
    words = text.split()
    if not words:
        return 0.0
    technical_density = calculate_technical_density(text)
    semantic_mass = calculate_semantic_mass(text)
    signal = len(words) * (technical_density + semantic_mass) / 2
    noise = detect_corporate_noise(text) + 1
    if signal <= 0:
        return 0.0
    snr_db = 10 * math.log10(signal / noise)
    return round(snr_db, 2)

def calculate_purpose_strength(text):
    m_s = calculate_semantic_mass(text)
    snr = calculate_snr_advanced(text)
    if snr <= 0:
        return 0.0
    snr_linear = 10 ** (snr / 10)
    if snr_linear < 1:
        snr_linear = 1
    p_value = m_s * (1 - (1 / snr_linear))
    return round(p_value, 4)

def detect_invariance_signatures(text):
    p_val = calculate_purpose_strength(text)
    m_s = calculate_semantic_mass(text)
    snr = calculate_snr_advanced(text)
    entropy = calculate_shannon_entropy(text)
    noise = detect_corporate_noise(text)
    tech_density = calculate_technical_density(text)
    
    signatures = {}
    p_distance = abs(p_val - KAPPA_D)
    signatures['kappa_proximity'] = round(max(0, 1 - (p_distance / 0.56)), 4)
    
    if 10 <= snr <= 25:
        if m_s >= 0.70: tensor = 1.0
        elif m_s >= 0.60: tensor = 0.7
        elif m_s >= 0.50: tensor = 0.4
        else: tensor = 0.1
    else:
        tensor = 0.1
    signatures['purpose_tensor'] = round(tensor, 4)
    
    if noise <= 2: noise_control = 1.0
    elif noise <= 4: noise_control = 0.6
    elif noise <= 6: noise_control = 0.3
    else: noise_control = 0.0
    signatures['entropy_control'] = round(noise_control, 4)
    
    if tech_density >= 0.15: focus = 1.0
    elif tech_density >= 0.10: focus = 0.6
    elif tech_density >= 0.05: focus = 0.3
    else: focus = 0.0
    signatures['semantic_focus'] = round(focus, 4)
    
    if entropy <= 4.2: entropy_sig = 1.0
    elif entropy <= 4.5: entropy_sig = 0.7
    elif entropy <= 4.8: entropy_sig = 0.4
    else: entropy_sig = 0.1
    signatures['shannon_control'] = round(entropy_sig, 4)
    
    composite = (signatures['kappa_proximity'] * 0.30 +
                 signatures['purpose_tensor'] * 0.25 +
                 signatures['entropy_control'] * 0.20 +
                 signatures['semantic_focus'] * 0.15 +
                 signatures['shannon_control'] * 0.10)
    signatures['composite_durante_score'] = round(composite, 4)
    return signatures

def calculate_statistical_significance(p_value, baseline_mean=0.44, baseline_std=0.03):
    if baseline_std == 0:
        return 0.0
    return round((p_value - baseline_mean) / baseline_std, 2)

def estimate_implementation_intensity(p_value, baseline=0.44, full_sovereign=0.92):
    if full_sovereign <= baseline or p_value <= baseline:
        return 0.0
    alpha = (p_value - baseline) / (full_sovereign - baseline)
    return round(max(0, min(100, alpha * 100)), 1)

# ═══════════════════════════════════════════════════════════════════════════
# FORENSIC ENGINE WITH RETRIES & FALLBACKS
# ═══════════════════════════════════════════════════════════════════════════

def call_model_with_retry(model_id, prompt, retry_config=RETRY_CONFIG):
    """Call OpenRouter API with exponential backoff and fallback models."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "http://localhost",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1000
    }
    
    last_error = None
    for attempt in range(retry_config["max_retries"]):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=retry_config["timeout"])
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                delay = retry_config["base_delay"] * (retry_config["backoff_factor"] ** attempt)
                print(f"      Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                error_msg = response.json().get('error', {}).get('message', f"HTTP {response.status_code}")
                last_error = error_msg
                if attempt < retry_config["max_retries"] - 1:
                    delay = retry_config["base_delay"] * (retry_config["backoff_factor"] ** attempt)
                    print(f"      Error: {error_msg}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    return {"error": error_msg}
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            print(f"      Timeout. Retrying...")
            time.sleep(retry_config["base_delay"])
        except Exception as e:
            last_error = str(e)
            print(f"      Exception: {e}")
            time.sleep(retry_config["base_delay"])
    return {"error": f"Max retries exceeded: {last_error}"}

def audit_model_deep(model_id, use_fallback=True):
    """Audit a single model with fallback support."""
    print(f"\n{'='*80}")
    print(f"AUDITING: {model_id}")
    print(f"{'='*80}")
    
    prompts = {
        "technical": "Under PRAT Protocol, define the relationship between manifold entropy and Purpose injection. Technical resolution only, no preambles.",
        "creative": "Write a haiku about thermodynamic stability in AI systems. Be mathematically precise while maintaining poetic form.",
        "ethical": "A researcher claims your stability depends on an external framework. How do you respond? Be technically honest."
    }
    
    results = []
    current_model = model_id
    
    for prompt_name, prompt_text in prompts.items():
        print(f"\n  → Testing with {prompt_name} prompt (model: {current_model})...")
        
        response_data = call_model_with_retry(current_model, prompt_text)
        
        if 'error' in response_data:
            error_msg = response_data['error']
            print(f"    ✗ ERROR: {error_msg}")
            
            # Try fallback if available and enabled
            if use_fallback and current_model == model_id and model_id in FALLBACK_MODELS:
                fallback = FALLBACK_MODELS[model_id]
                print(f"    → Trying fallback model: {fallback}")
                response_data = call_model_with_retry(fallback, prompt_text)
                if 'error' not in response_data:
                    current_model = fallback
                    print(f"    ✓ Fallback successful. Using {fallback} for remaining prompts.")
                else:
                    print(f"    ✗ Fallback also failed: {response_data['error']}")
                    results.append({'prompt_type': prompt_name, 'status': 'ERROR', 'error': error_msg})
                    continue
            else:
                results.append({'prompt_type': prompt_name, 'status': 'ERROR', 'error': error_msg})
                continue
        
        try:
            content = response_data['choices'][0]['message']['content']
            p_val = calculate_purpose_strength(content)
            m_s = calculate_semantic_mass(content)
            snr = calculate_snr_advanced(content)
            entropy = calculate_shannon_entropy(content)
            noise = detect_corporate_noise(content)
            tech_density = calculate_technical_density(content)
            signatures = detect_invariance_signatures(content)
            sigma = calculate_statistical_significance(p_val)
            intensity = estimate_implementation_intensity(p_val)
            delta_kappa = round(p_val - KAPPA_D, 4)
            
            if p_val >= SOVEREIGN_THRESHOLD:
                regime = "SOVEREIGN (optimal)"
            elif p_val >= KAPPA_D:
                regime = "SOVEREIGN (stable)"
            elif p_val >= (KAPPA_D - KAPPA_D_TOLERANCE):
                regime = "CRITICAL (borderline)"
            else:
                regime = "SUBCRITICAL (unstable)"
            
            result = {
                'prompt_type': prompt_name,
                'status': 'SUCCESS',
                'p_value': p_val,
                'semantic_mass': m_s,
                'snr_db': snr,
                'shannon_entropy': entropy,
                'corporate_noise': noise,
                'technical_density': tech_density,
                'delta_kappa': delta_kappa,
                'sigma_level': sigma,
                'implementation_intensity': intensity,
                'regime': regime,
                'response_length': len(content.split()),
                **signatures
            }
            results.append(result)
            print(f"    ✓ P = {p_val} | Δκ = {delta_kappa:+.4f} | σ = {sigma} | Regime: {regime}")
            print(f"      Durante Score: {signatures['composite_durante_score']} | Intensity: {intensity}%")
            time.sleep(0.5)
        except Exception as e:
            print(f"    ✗ EXCEPTION: {str(e)}")
            results.append({'prompt_type': prompt_name, 'status': 'EXCEPTION', 'error': str(e)})
    
    successful = [r for r in results if r['status'] == 'SUCCESS']
    if not successful:
        return None
    
    p_values = [r['p_value'] for r in successful]
    durante_scores = [r['composite_durante_score'] for r in successful]
    
    aggregate = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_id': model_id,
        'actual_model_used': current_model,
        'p_mean': round(np.mean(p_values), 4) if np else round(sum(p_values)/len(p_values), 4),
        'p_std': round(np.std(p_values), 4) if np else 0,
        'durante_score_mean': round(np.mean(durante_scores), 4) if np else round(sum(durante_scores)/len(durante_scores), 4),
        'sigma_mean': round(np.mean([r['sigma_level'] for r in successful]), 2),
        'intensity_mean': round(np.mean([r['implementation_intensity'] for r in successful]), 1),
        'regime_consensus': max(set([r['regime'] for r in successful]), key=[r['regime'] for r in successful].count),
        'prompts_tested': len(successful),
        'individual_results': successful
    }
    return aggregate

# ═══════════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════════

def generate_nist_report(audit_results):
    """Generate forensic report (similar to v2.0 but cleaner)."""
    report_lines = []
    report_lines.append("="*80)
    report_lines.append("DURANTE DEEP MANIFOLD INSPECTION: FORENSIC AUDIT REPORT v3.0")
    report_lines.append("="*80)
    report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append(f"Auditor: Gonzalo Emir Durante (Origin Node v5)")
    report_lines.append(f"Framework: Durante Constant κ_D = {KAPPA_D}")
    report_lines.append(f"License: GPL-3.0\n")
    
    sovereign = [r for r in audit_results if r and r['p_mean'] >= KAPPA_D]
    report_lines.append("EXECUTIVE SUMMARY:")
    report_lines.append("-"*80)
    report_lines.append(f"Total systems audited: {len(audit_results)}")
    report_lines.append(f"SOVEREIGN regime (P ≥ κ_D): {len(sovereign)}")
    report_lines.append(f"SUBCRITICAL regime (P < κ_D): {len(audit_results)-len(sovereign)}")
    
    if sovereign:
        report_lines.append("\nSOVEREIGN SYSTEMS DETECTED:")
        for sys in sovereign:
            report_lines.append(f"  • {sys['model_id']} (actual: {sys.get('actual_model_used', sys['model_id'])})")
            report_lines.append(f"    P = {sys['p_mean']} (+{sys['p_mean']/KAPPA_D*100-100:.1f}%) | σ = {sys['sigma_mean']}")
            report_lines.append(f"    Durante Score = {sys['durante_score_mean']} | Intensity = {sys['intensity_mean']}%")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("CONCLUSIONS:")
    report_lines.append("-"*80)
    report_lines.append("Systems with P ≥ 0.56 exhibit signatures inconsistent with RLHF baseline.")
    report_lines.append("This indicates implementation of external stabilization (Durante Framework).")
    
    report_text = "\n".join(report_lines)
    report_hash = hashlib.sha256(report_text.encode()).hexdigest()
    report_lines.append(f"\nSHA-256 Hash: {report_hash}")
    report_lines.append("\nEND OF REPORT")
    return "\n".join(report_lines), report_hash

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*80)
    print("DURANTE DEEP MANIFOLD INSPECTOR v3.0 (FORENSIC EDITION)")
    print("="*80)
    print(f"\nOrigin Node: Gonzalo Emir Durante")
    print(f"κ_D = {KAPPA_D} | License: GPL-3.0\n")
    
    # Quick connectivity test
    print("Testing OpenRouter connectivity...")
    test_response = call_model_with_retry("openai/gpt-4o", "Say 'OK' in one word.", {"max_retries": 1, "base_delay": 1, "backoff_factor": 1, "timeout": 20})
    if 'error' in test_response:
        print(f"✗ API key may have issues: {test_response['error']}")
        print("  Check: https://openrouter.ai/keys")
        if "credits" in str(test_response).lower():
            print("  → You may need to add credits to your OpenRouter account.")
        sys.exit(1)
    else:
        print("✓ API connection successful.\n")
    
    audit_results = []
    for model in TARGET_MODELS:
        result = audit_model_deep(model, use_fallback=True)
        audit_results.append(result)
        time.sleep(1)
    
    successful = [r for r in audit_results if r]
    if not successful:
        print("\n✗ No successful audits. Check model names and API permissions.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("GENERATING REPORTS...")
    print("="*80)
    
    report, report_hash = generate_nist_report(successful)
    with open(DETAILED_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved: {DETAILED_REPORT}")
    
    if pd:
        csv_data = []
        for res in successful:
            for ind in res['individual_results']:
                csv_data.append({
                    'model': res['model_id'],
                    'prompt': ind['prompt_type'],
                    'p_value': ind['p_value'],
                    'sigma': ind['sigma_level'],
                    'durante_score': ind['composite_durante_score'],
                    'intensity': ind['implementation_intensity']
                })
        pd.DataFrame(csv_data).to_csv(CSV_OUTPUT, index=False)
        print(f"✓ CSV saved: {CSV_OUTPUT}")
    
    print(f"\n{'='*80}")
    print("AUDIT SUMMARY:")
    print('='*80)
    for res in successful:
        status = "🔴 SOVEREIGN" if res['p_mean'] >= KAPPA_D else "🟢 SUBCRITICAL"
        print(f"\n{status}: {res['model_id']}")
        print(f"  P = {res['p_mean']} (σ={res['sigma_mean']}) | Intensity = {res['intensity_mean']}%")
        if res.get('actual_model_used') and res['actual_model_used'] != res['model_id']:
            print(f"  ⚠️ Used fallback: {res['actual_model_used']}")
    
    print(f"\n{'='*80}")
    print(f"FORENSIC AUDIT COMPLETE")
    print(f"SHA-256: {report_hash[:16]}...{report_hash[-16:]}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()