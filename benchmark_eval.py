import nltk
import numpy as np
import json
import math
import re
import collections
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from nltk.corpus import cmudict
import textstat

nltk.download('punkt')
nltk.download('cmudict')

class StoryEvaluator:
    def __init__(self):
        try:
            self.d = cmudict.dict()  # For calculating syllables
        except LookupError:
            print("Downloading cmudict...")
            nltk.download('cmudict')
            self.d = cmudict.dict()
    
    def evaluate_story(self, text):
        """Evaluate various metrics of story text"""
        # Preprocess text - use simple sentence splitting method to replace sent_tokenize
        sentences = re.split(r'(?<=[.!?])\s+', text)
        words = word_tokenize(text.lower())
        # Filter punctuation marks
        words = [word for word in words if word.isalpha()]
        
        # Calculate various metrics
        results = {
            "flesch_kincaid": self._calculate_flesch_kincaid(text),
            "distinct_1": self._calculate_distinct_n(words, 1),
            "distinct_2": self._calculate_distinct_n(words, 2),
            "perplexity": self._calculate_perplexity(words),
        }
        
        return results
    
    def _calculate_flesch_kincaid(self, text):
        """Calculate Flesch-Kincaid readability index"""
        return textstat.flesch_kincaid_grade(text)
    
    def _calculate_distinct_n(self, words, n):
        """Calculate Distinct-n metric"""
        if len(words) < n:
            return 0
        ngram_list = list(ngrams(words, n))
        if not ngram_list:
            return 0
        return len(set(ngram_list)) / len(ngram_list)
    
    def _calculate_perplexity(self, words):
        """
        Calculate perplexity
        Use simplified method: estimate through word frequency distribution
        """
        if len(words) < 10:  # Text too short
            return float('inf')
            
        # Use simple method: entropy calculation based on word frequency statistics
        freq_dist = collections.Counter(words)
        total_words = len(words)
        
        # Calculate entropy
        entropy = 0
        for word, count in freq_dist.items():
            prob = count / total_words
            entropy -= prob * math.log2(prob)
        
        # Perplexity = 2^entropy
        return math.pow(2, entropy) / 10

def evaluate_text(story_text):
    """Evaluate given text and return various metrics"""
    evaluator = StoryEvaluator()
    results = evaluator.evaluate_story(story_text)
    
    return results


ap_fk = 0
ap_dist1 = 0
ap_dist2 = 0
ap_perplexity = 0
direct_fk = 0
direct_dist1 = 0
direct_dist2 = 0
direct_perplexity = 0

# Evaluate stories
temp = ['drone_', 'earphone_', 'smartphone_']

for i in temp:
    for j in range(10):
        file_name = "samples/" + i + str(j) + '.json'
        with open(file_name, 'r') as f:
            data = json.load(f)
            ap_story = data[0]["story"]
            direct_story = data[1]["story"]
            ap_benchmark = evaluate_text(ap_story)
            direct_benchmark = evaluate_text(direct_story)
            ap_fk += ap_benchmark["flesch_kincaid"]
            ap_dist1 += ap_benchmark["distinct_1"]
            ap_dist2 += ap_benchmark["distinct_2"]
            ap_perplexity += ap_benchmark["perplexity"]
            direct_fk += direct_benchmark["flesch_kincaid"]
            direct_dist1 += direct_benchmark["distinct_1"]
            direct_dist2 += direct_benchmark["distinct_2"]
            direct_perplexity += direct_benchmark["perplexity"]

print("AP-based flesch kincaid: " + str(ap_fk/30))
print("AP-based distinct_1: " + str(ap_dist1/30))
print("AP-based distinct_2: " + str(ap_dist2/30))
print("AP-based perplexity: " + str(ap_perplexity/30))
print("Direct flesch kincaid: " + str(direct_fk/30))
print("Direct distinct_1: " + str(direct_dist1/30))
print("Direct distinct_2: " + str(direct_dist2/30))
print("Direct perplexity: " + str(direct_perplexity/30))