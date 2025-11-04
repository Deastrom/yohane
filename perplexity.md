Here’s a focused roadmap to genuinely **improve yohane for English singing karaoke alignment**—balancing practical engineering and research-grade techniques:

***

### **1. Upgrade Syllable Splitting for English (Baseline Improvement)**
- **Swap the Japanese syllable splitter for an English solution.** Start simple:
  - Use a Python library like `eng-syl` (GRU-based) or `syllabreak`/`pyphen` for rule-based segmentation.
  - Integrate in yohane as a language check: `--language en` calls the correct splitter.
  - Build unit tests with well-known English karaoke lyrics to validate segmentation output against ground truth.

***

### **2. Add Singing-Specific Post-Processing (Critical for Real Karaoke)**
- **Address differences between speech and singing:** Implement heuristics that:
  - Merge or ignore syllable boundaries inside elongated vowels (common in singing).
  - Adjust timing so boundaries match vocal phrasing, especially for “melisma” (one syllable across several notes).
  - Discard false boundaries introduced by vibrato effects.

***

### **3. Test and Compare Against Research Models**
- **Evaluate your improvements versus “regular speech” models and published singing models:**
  - Use open datasets (like DAMP, MIR-1K) or annotate a few tracks manually for validation.
  - If possible, experiment with open-source phoneme segmentation models for singing (Gong & Serra 2018, or the STARS Framework from 2025).
    - Incorporate only the phoneme onset detection if full integration is too complex.

***

### **4. Improve the Alignment Pipeline**
- **Check yohane’s alignment with Torchaudio:**
  - Make sure forced alignment is using an acoustic model trained (or at least robust) for singing, not just speech.
  - If your tests show poor timing, try fine-tuning a Wav2Vec2 or HuBERT model on a small set of singing audio.

***

### **5. Usability & Contribution**
- **Make English support a first-class feature:**
  - Clear CLI flag for language choice
  - Add documentation and sample usage for English tracks—highlight known limitations and how to fix them in Aegisub
  - Encourage user feedback with examples and issues template (let the community converge on best practices)

***

**Best Starting Point:**  
Modify the syllable splitting logic and test on actual sung English tracks. Then add singing-aware heuristics (vowel merging, vibrato filtering). Document everything, and submit incremental improvements in your PR—invite others to help with more advanced model integration later.

**Key Philosophy:**  
*Optimize for real singing, not just speech—so always test with English karaoke vocals, not only text.* Get the basics right, and build toward research-grade segmentation as the community and tools evolve.