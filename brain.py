# -*- coding: utf-8 -*-
"""
brain.py — Jarvis Conversational Brain v3
Inspired by: NLTK TF-IDF chatbots, Rasa NLU intent scoring, ELIZA pattern matching
Techniques used:
  - TF-IDF + Cosine Similarity for semantic understanding (no API needed)
  - Conversation context tracking (remembers last topic, last answer)
  - Named entity extraction (who/what/where/when)
  - Follow-up question handling (tell me more, why, example)
  - Personality layer (greetings, emotions, jokes, opinions)
  - Smart fallback using memory search
"""

import re
import math
import random
import string
from collections import Counter
from memory import Memory


# ─────────────────────────────────────────────────────────────────────────────
#  STOP WORDS — common words that carry no meaning for matching
# ─────────────────────────────────────────────────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for", "of",
    "and", "or", "but", "i", "you", "he", "she", "we", "they", "do",
    "did", "does", "has", "have", "had", "be", "am", "are", "was", "were",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "not", "no", "so", "if", "as", "by", "from", "with", "this", "that",
    "these", "those", "my", "your", "his", "her", "its", "our", "their",
    "me", "him", "us", "them", "what", "which", "who", "whom", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "than", "too", "very", "just", "about", "up", "out", "then", "now",
    "also", "like", "into", "over", "after", "before", "because", "some",
    "get", "got", "let", "go", "come", "make", "say", "know", "think",
    "want", "need", "see", "look", "use", "take", "give", "well", "back",
    "even", "still", "way", "down", "only", "own", "same", "here", "there",
    "tell", "little", "good", "great", "much", "many",
}

# ─────────────────────────────────────────────────────────────────────────────
#  INTENTS — now with confidence weights, not just keyword lists
#  Format: (pattern_regex, intent_name, confidence)
# ─────────────────────────────────────────────────────────────────────────────
INTENT_PATTERNS = [
    # Greetings
    (r"^(hi|hey|hello|hiya|howdy|sup|yo|good morning|good afternoon|good evening|what'?s up)[!.,]?$", "greet", 1.0),
    (r"\b(hi|hey|hello)\b", "greet", 0.6),

    # Identity / what are you
    (r"(who|what) are you|your name|introduce yourself|tell me about yourself|are you (a bot|an ai|real|human)", "identity", 1.0),
    (r"(what (kind|type) of|are you a)", "identity", 0.7),

    # How are you / feelings
    (r"how are you|how('?re| is it going)|you (good|okay|alright|doing)", "feelings", 1.0),

    # Compliments
    (r"(you'?re|you are) (great|amazing|smart|awesome|brilliant|incredible|the best|good|helpful)", "compliment", 1.0),
    (r"(good|great|nice|well) (job|done|work|going)", "compliment", 0.9),

    # Thanks
    (r"\b(thank(s| you)|thx|ty|cheers|appreciate( it| that)?)\b", "thanks", 1.0),

    # Status / learning progress
    (r"(status|stats|how (much|many|smart)|what (have|did) you learn|progress|how (much do you know|far have you gone))", "status", 1.0),

    # Follow-ups — these MUST come before generic question patterns
    (r"(^tell me more|more details|more info|explain|expand|go deeper|give me more)$", "more", 1.0),
    (r"^why(\?|$)|why (is|does|do|was|are|did)|how come|what'?s the reason", "why", 1.0),
    (r"(give (me )?an? example|for example|such as|like what|can you show|example of)", "example", 1.0),

    # Opinion
    (r"(what do you think|your opinion|do you (think|believe|feel)|in your opinion|what'?s your view)", "opinion", 1.0),

    # Jokes
    (r"(tell me a joke|say something funny|make me laugh|\bjoke\b|something funny)", "joke", 1.0),

    # Learn / teach
    (r"(learn|study|research|read|find out|teach yourself|get info|look into|explore).{0,20}(about|on)", "learn", 1.0),
    (r"^(learn|study|research) ", "learn", 0.9),

    # Questions — what/who/how/when/where/why
    (r"^(what is|what are|what was|what were|what does|what do)\b", "question", 1.0),
    (r"^(who is|who was|who are|who were|who did|who invented|who created)\b", "question", 1.0),
    (r"^(how does|how do|how is|how are|how was|how were|how did|how can)\b", "question", 1.0),
    (r"^(when (is|was|did|were|are)|where (is|was|are|were))\b", "question", 1.0),
    (r"^(explain|describe|define|tell me (about|what)|give me info)\b", "question", 1.0),
    (r"(do you know (about|what|who|how)|can you explain|i want to know|i'?m curious about)", "question", 0.9),
    (r"\?$", "question", 0.7),

    # Search
    (r"(search (for|the web for)|look up|google|find (info|results|pages)|browse for|show me results)", "search", 1.0),

    # Scrape
    (r"(scrape|get text from|read (the )?page|fetch|extract from) https?://", "scrape", 1.0),

    # Navigate / browser
    (r"(go to|navigate to|visit|open url|browse to|take me to) https?://", "navigate", 1.0),
    (r"(go to|navigate to|open url|take me to) \S+\.\S+", "navigate", 0.9),

    # Desktop
    (r"(take a? screenshot|capture (the )?screen|screen(shot| capture))", "screenshot", 1.0),
    (r"^(open|launch|start|bring up) [a-zA-Z]", "open_app", 1.0),
    (r"^(type|write|input) [\"']?.+", "type_text", 1.0),
    (r"(press|hit) (ctrl|alt|shift|enter|escape|tab|space)", "hotkey", 1.0),
    (r"(ctrl|alt|shift)\+\w", "hotkey", 1.0),
    (r"(run (command|script)|shell|execute|terminal|cmd) ", "shell", 1.0),

    # Learning control
    (r"(stop|pause) (learning|crawling)", "stop_learning", 1.0),
    (r"(start|resume|continue) (learning|crawling)", "resume_learning", 1.0),

    # Help
    (r"(help|what can you do|commands|capabilities|how do i use you|guide me)", "help", 1.0),

    # Clear
    (r"(forget (our conversation|everything)|clear (history|chat)|start over|reset chat)", "clear_history", 1.0),

    # Goodbye
    (r"^(bye|goodbye|see you|farewell|take care|later|exit|quit)[\s!.,]?$", "bye", 1.0),

    # Name introduction
    (r"(my name is|i am|i'?m|call me) ([A-Za-z]+)", "introduce", 1.0),
]

# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE BANKS — varied responses to avoid repetition
# ─────────────────────────────────────────────────────────────────────────────
GREETINGS = [
    "Hey! What's on your mind?",
    "Hello! What would you like to know?",
    "Hi there! What can I do for you?",
    "Hey! I'm here and ready. What do you want to talk about?",
    "Yo! What's up? Ask me anything.",
]

THINKING = [
    "Here's what I know about that:",
    "Good question. Based on what I've read:",
    "Let me pull that up from memory:",
    "Here's what I found:",
    "Based on everything I've learned:",
]

MORE = [
    "Sure! Here's more:",
    "Of course — digging deeper:",
    "Happy to elaborate:",
    "Here's additional detail:",
]

CONFUSED = [
    "Hmm, I'm not quite sure what you mean. Try rephrasing?",
    "I didn't fully catch that. Can you say it differently?",
    "Not sure I understand — could you be more specific?",
    "I'm still learning! Try asking in a different way.",
]

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why was the computer cold? It left its Windows open.",
    "There are 10 types of people: those who understand binary, and those who don't.",
    "I would tell you a joke about UDP... but you might not get it.",
    "Why don't scientists trust atoms? Because they make up everything!",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
]


# ─────────────────────────────────────────────────────────────────────────────
#  TF-IDF ENGINE — understands meaning, not just keywords
# ─────────────────────────────────────────────────────────────────────────────
class TFIDF:
    """
    Lightweight TF-IDF + Cosine Similarity engine.
    Inspired by sklearn's TfidfVectorizer but with zero dependencies.
    Used to find the most semantically relevant memory result for any query.
    """

    def tokenize(self, text: str) -> list:
        """Clean, lowercase, remove stop words, return word tokens."""
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = text.split()
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

    def tf(self, tokens: list) -> dict:
        """Term Frequency: how often each word appears in this document."""
        count = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: count[word] / total for word in count}

    def idf(self, word: str, documents: list) -> float:
        """Inverse Document Frequency: how rare a word is across all docs."""
        containing = sum(1 for doc in documents if word in doc)
        if containing == 0:
            return 0.0
        return math.log(len(documents) / containing) + 1

    def tfidf_vector(self, tokens: list, all_doc_tokens: list) -> dict:
        """Build TF-IDF vector for a document."""
        tf_vals = self.tf(tokens)
        return {
            word: tf_vals[word] * self.idf(word, all_doc_tokens)
            for word in tf_vals
        }

    def cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Cosine similarity between two TF-IDF vectors."""
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0
        dot = sum(vec1[w] * vec2[w] for w in common)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def best_match(self, query: str, documents: list, threshold: float = 0.05):
        """
        Find the most semantically similar document to the query.
        Returns (best_doc, score) or (None, 0) if nothing matches well enough.
        """
        if not documents:
            return None, 0.0

        q_tokens = self.tokenize(query)
        doc_token_lists = [self.tokenize(d["content"]) for d in documents]
        all_tokens = doc_token_lists + [q_tokens]

        q_vec = self.tfidf_vector(q_tokens, all_tokens)

        best_doc = None
        best_score = 0.0
        for i, doc in enumerate(documents):
            d_vec = self.tfidf_vector(doc_token_lists[i], all_tokens)
            score = self.cosine_similarity(q_vec, d_vec)
            if score > best_score:
                best_score = score
                best_doc = doc

        if best_score >= threshold:
            return best_doc, best_score
        return None, 0.0


# ─────────────────────────────────────────────────────────────────────────────
#  BRAIN
# ─────────────────────────────────────────────────────────────────────────────
class Brain:
    def __init__(self, memory: Memory):
        self.memory = memory
        self.tfidf = TFIDF()

        # Conversation state
        self.history = []        # [(user_msg, jarvis_reply), ...]
        self.last_topic = None   # Last topic discussed
        self.last_answer = None  # Last answer given
        self.last_results = []   # Last memory results fetched
        self.user_name = None    # User's name if they told us

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN ENTRY
    # ─────────────────────────────────────────────────────────────────────────
    def think(self, user_input: str) -> dict:
        raw = user_input.strip()
        lower = raw.lower().strip()

        # Detect name introduction anywhere in input
        name_m = re.search(r"(?:my name is|i am|i'?m|call me)\s+([a-zA-Z]+)", lower)
        if name_m:
            self.user_name = name_m.group(1).capitalize()

        intent, confidence = self._detect_intent(lower)
        response = self._route(intent, confidence, raw, lower)

        # Save to conversation history
        if isinstance(response, str):
            self.history.append((raw, response))
            if len(self.history) > 30:
                self.history = self.history[-30:]
            return {"action": "respond", "params": {}, "response": response}

        # Response is an action dict (for learn, search, desktop, etc.)
        reply_text = response.get("response", "")
        self.history.append((raw, reply_text))
        return response

    # ─────────────────────────────────────────────────────────────────────────
    #  INTENT DETECTION — regex patterns with confidence scores
    # ─────────────────────────────────────────────────────────────────────────
    def _detect_intent(self, lower: str):
        """
        Match input against all intent patterns.
        Returns (intent_name, confidence).
        Higher confidence patterns win ties.
        """
        best_intent = "unknown"
        best_conf = 0.0

        for pattern, intent, conf in INTENT_PATTERNS:
            if re.search(pattern, lower):
                if conf > best_conf:
                    best_conf = conf
                    best_intent = intent

        return best_intent, best_conf

    # ─────────────────────────────────────────────────────────────────────────
    #  ROUTING
    # ─────────────────────────────────────────────────────────────────────────
    def _route(self, intent: str, confidence: float, raw: str, lower: str):

        if intent == "greet":
            n = f" {self.user_name}!" if self.user_name else "!"
            return random.choice(GREETINGS).rstrip("!") + n

        if intent == "introduce":
            return (
                f"Nice to meet you, {self.user_name}! "
                f"I'm Jarvis. What would you like to know?"
            )

        if intent == "identity":
            return self._identity()

        if intent == "feelings":
            stats = self.memory.stats()
            return (
                f"I'm doing great, thanks for asking! "
                f"I've learned {stats['total_facts']} facts from "
                f"{stats['urls_visited']} pages so far and still going strong. "
                f"How about you?"
            )

        if intent == "compliment":
            return random.choice([
                "Aw, thank you! I'm doing my best to be as helpful as possible.",
                "That means a lot! I'm learning more every second.",
                "Thanks! I'm always trying to improve. What can I help you with?",
                "You're too kind! Now — what would you like to know?",
            ])

        if intent == "thanks":
            return random.choice([
                "Happy to help! What else would you like to know?",
                "Anytime! That's what I'm here for.",
                "No problem at all! What's next?",
                "Glad I could help! Keep the questions coming.",
            ])

        if intent == "joke":
            return random.choice(JOKES)

        if intent == "bye":
            n = f", {self.user_name}" if self.user_name else ""
            return f"Goodbye{n}! I'll keep learning while you're away. Talk soon!"

        if intent == "status":
            return "status"

        if intent == "help":
            return self._help()

        if intent == "clear_history":
            self.history.clear()
            self.last_topic = None
            self.last_answer = None
            self.last_results = []
            return "Done! Fresh start. What would you like to talk about?"

        if intent == "stop_learning":
            return {"action": "stop_learning", "params": {}, "response": "Pausing background learning."}

        if intent == "resume_learning":
            return {"action": "resume_learning", "params": {}, "response": "Resuming background learning!"}

        if intent == "more":
            return self._tell_more()

        if intent == "why":
            # Extract the subject of the "why" question
            subject = re.sub(r"^(why (is|does|do|was|are|did)|how come|what'?s the reason (for|why)?)\s*", "", lower).strip()
            return self._answer(subject or self.last_topic or lower, mode="why")

        if intent == "example":
            subject = re.sub(r"^(give (me )?an? example (of)?|example of|such as|like what)\s*", "", lower).strip()
            return self._answer(subject or self.last_topic or lower, mode="example")

        if intent == "opinion":
            subject = re.sub(r"^(what do you think (about)?|your opinion (on)?|do you (think|believe|feel) (about)?|in your opinion)\s*", "", lower).strip()
            return self._answer(subject or lower, mode="opinion")

        if intent == "learn":
            topic = self._extract_topic_from_learn(lower)
            if not topic or len(topic) < 2:
                return "What should I learn about? Example: 'learn about quantum computing'"
            self.last_topic = topic
            return {
                "action": "learn_topic",
                "params": {"topic": topic},
                "response": (
                    f"On it! Searching the web for '{topic}' right now.\n"
                    f"Give me about 30 seconds, then ask me about it!"
                ),
            }

        if intent == "question":
            query = self._extract_question_subject(lower)
            return self._answer(query)

        if intent == "search":
            query = re.sub(
                r"(search (for|the web for)|look up|google|find (info|results|pages) (about|on|for)?|browse for|show me results (for|about)?)\s*",
                "", lower
            ).strip()
            return {
                "action": "scrape",
                "params": {"mode": "search", "query": query},
                "response": f"Searching the web for: {query}",
            }

        if intent == "scrape":
            url = _extract_url(raw)
            return {"action": "scrape", "params": {"mode": "text", "url": url}, "response": f"Reading: {url}"}

        if intent == "navigate":
            url = _extract_url(raw) or re.sub(r".*(go to|navigate to|visit|open url|take me to)\s*", "", lower).strip()
            return {"action": "browser", "params": {"cmd": "go", "url": url}, "response": f"Opening {url}"}

        if intent == "screenshot":
            return {"action": "desktop", "params": {"cmd": "screenshot"}, "response": "Taking screenshot."}

        if intent == "open_app":
            app = re.sub(r"^(open|launch|start|bring up)\s+", "", lower).strip()
            return {"action": "desktop", "params": {"cmd": "open", "app": app}, "response": f"Opening {app}."}

        if intent == "type_text":
            text = _extract_quoted(raw) or re.sub(r"^(type|write|input)\s+", "", raw).strip()
            return {"action": "desktop", "params": {"cmd": "type", "text": text}, "response": f"Typing: {text}"}

        if intent == "hotkey":
            keys = _extract_hotkey(lower)
            return {"action": "desktop", "params": {"cmd": "hotkey", "keys": keys}, "response": f"Pressing {'+'.join(keys)}."}

        if intent == "shell":
            cmd = re.sub(r"^(run (command|script)|shell|execute|terminal|cmd)\s+", "", raw).strip()
            return {"action": "desktop", "params": {"cmd": "run", "command": cmd}, "response": "Running command."}

        # ── UNKNOWN — use TF-IDF to find the best memory match ────────────────
        return self._smart_search(raw, lower)

    # ─────────────────────────────────────────────────────────────────────────
    #  SMART SEARCH — TF-IDF against all memory when intent is unknown
    # ─────────────────────────────────────────────────────────────────────────
    def _smart_search(self, raw: str, lower: str) -> str:
        """
        For any input that doesn't match a clear intent,
        use TF-IDF cosine similarity to find the best memory match.
        This is how retrieval-based chatbots work.
        """
        # Pull broad results from memory using keyword search
        results = self.memory.search(lower, limit=10)

        if results:
            best, score = self.tfidf.best_match(lower, results)
            if best and score > 0.03:
                summary = self._smart_summarize(best["content"], lower)
                self.last_topic = lower
                self.last_answer = summary
                self.last_results = results
                return (
                    f"{random.choice(THINKING)}\n\n"
                    f"{summary}\n\n"
                    f"Source: {best['url']}\n"
                    f"(Say 'tell me more' for more details)"
                )

        # Nothing in memory — be helpful about it
        return (
            f"{random.choice(CONFUSED)}\n\n"
            f"If you're asking about a topic, try:\n"
            f"  'What is [topic]?'\n"
            f"  'Learn about [topic]'\n"
            f"  'Search for [topic]'\n"
            f"Or just chat with me!"
        )

    # ─────────────────────────────────────────────────────────────────────────
    #  ANSWER — core question answering using memory + TF-IDF
    # ─────────────────────────────────────────────────────────────────────────
    def _answer(self, query: str, mode: str = "normal") -> str:
        if not query or len(query) < 2:
            query = self.last_topic or "that"

        # Fetch candidates from memory
        results = self.memory.search(query, limit=10)

        if not results:
            self.last_topic = query
            return (
                f"I haven't learned about '{query}' yet.\n"
                f"Want me to go find out? Say: 'learn about {query}'"
            )

        # Use TF-IDF to pick the most semantically relevant result
        best, score = self.tfidf.best_match(query, results)
        if not best:
            best = results[0]

        self.last_topic = query
        self.last_results = results

        if mode == "why":
            summary = self._extract_sentences(best["content"], query, ["because", "since", "therefore", "thus", "reason", "cause", "result"])
            prefix = "Here's why:\n\n"
        elif mode == "example":
            summary = self._extract_sentences(best["content"], query, ["example", "such as", "for instance", "like", "including", "e.g"])
            prefix = "Here's an example:\n\n"
        elif mode == "opinion":
            summary = self._smart_summarize(best["content"], query)
            prefix = f"Based on what I've read about '{query}':\n\n"
        else:
            summary = self._smart_summarize(best["content"], query)
            prefix = f"{random.choice(THINKING)}\n\n"

        self.last_answer = summary

        source_note = ""
        if len(results) > 1:
            source_note = f"\n\n(Found {len(results)} sources. Say 'tell me more' for additional details.)"

        name = f"{self.user_name}, " if self.user_name else ""
        return f"{name}{prefix}{summary}\n\nSource: {best['url']}{source_note}"

    # ─────────────────────────────────────────────────────────────────────────
    #  TELL ME MORE — pulls from other sources on same topic
    # ─────────────────────────────────────────────────────────────────────────
    def _tell_more(self) -> str:
        if not self.last_topic:
            return "What would you like to know more about? We haven't discussed a topic yet!"

        results = self.last_results or self.memory.search(self.last_topic, limit=10)

        if not results:
            return f"I don't have more info on '{self.last_topic}'. Say 'learn about {self.last_topic}' to dig deeper!"

        # Find a result different from what we already showed
        extra_parts = []
        for r in results[1:4]:
            summary = self._smart_summarize(r["content"], self.last_topic)
            if summary and summary != self.last_answer and len(summary) > 50:
                extra_parts.append(f"From {r['url']}:\n{summary}")

        if not extra_parts:
            # Try pulling more sentences from the best result
            best = results[0]
            sentences = re.split(r'(?<=[.!?])\s+', best["content"])
            extras = [s.strip() for s in sentences[5:10] if len(s.strip()) > 40]
            if extras:
                extra_parts = [" ".join(extras)]

        if extra_parts:
            return f"{random.choice(MORE)}\n\n" + "\n\n---\n\n".join(extra_parts)

        return f"That's all I have on '{self.last_topic}' right now. Say 'learn about {self.last_topic}' for more!"

    # ─────────────────────────────────────────────────────────────────────────
    #  SUMMARIZERS
    # ─────────────────────────────────────────────────────────────────────────
    def _smart_summarize(self, content: str, query: str, max_chars: int = 500) -> str:
        """
        Rank sentences by TF-IDF relevance to query.
        Pick top N that together make a coherent answer under max_chars.
        """
        sentences = re.split(r'(?<=[.!?])\s+', content)
        q_tokens = self.tfidf.tokenize(query)
        q_set = set(q_tokens)

        def score(s):
            s_tokens = self.tfidf.tokenize(s)
            return len(q_set & set(s_tokens))

        ranked = sorted(
            [(score(s), s.strip()) for s in sentences if len(s.strip()) > 40],
            key=lambda x: x[0], reverse=True
        )

        result = []
        total = 0
        for _, sent in ranked[:6]:
            if total + len(sent) > max_chars:
                break
            result.append(sent)
            total += len(sent)

        return " ".join(result) if result else content[:max_chars]

    def _extract_sentences(self, content: str, query: str, signal_words: list, max_chars: int = 500) -> str:
        """Extract sentences that contain signal words (for why/example modes)."""
        sentences = re.split(r'(?<=[.!?])\s+', content)
        q_tokens = set(self.tfidf.tokenize(query))

        matched = [
            s.strip() for s in sentences
            if any(w in s.lower() for w in signal_words)
            and len(s.strip()) > 40
        ]

        if not matched:
            return self._smart_summarize(content, query, max_chars)

        result = []
        total = 0
        for s in matched[:5]:
            if total + len(s) > max_chars:
                break
            result.append(s)
            total += len(s)

        return " ".join(result)

    # ─────────────────────────────────────────────────────────────────────────
    #  TOPIC EXTRACTORS
    # ─────────────────────────────────────────────────────────────────────────
    def _extract_topic_from_learn(self, lower: str) -> str:
        patterns = [
            r"learn(?: more)? about (.+)",
            r"study (.+)",
            r"research (.+)",
            r"read about (.+)",
            r"find out about (.+)",
            r"teach yourself(?: about)? (.+)",
            r"get info(?:rmation)? on (.+)",
            r"look into (.+)",
            r"explore (.+)",
            r"go learn(?: about)? (.+)",
        ]
        for p in patterns:
            m = re.search(p, lower)
            if m:
                return m.group(1).strip().strip("\"'.,!?")
        # Fallback: strip common learn verbs
        return re.sub(r"^(learn|study|research|explore)\s+", "", lower).strip()

    def _extract_question_subject(self, lower: str) -> str:
        patterns = [
            r"^what (?:is|are|was|were|does|do) (.+?)[\?.]?$",
            r"^who (?:is|was|are|were|did|invented|created) (.+?)[\?.]?$",
            r"^how (?:does|do|is|are|was|were|did|can) (.+?)[\?.]?$",
            r"^when (?:is|was|did|were|are) (.+?)[\?.]?$",
            r"^where (?:is|was|are|were) (.+?)[\?.]?$",
            r"^(?:explain|describe|define) (.+?)[\?.]?$",
            r"^tell me (?:about|what) (.+?)[\?.]?$",
            r"^(?:give me info|give me information) (?:on|about) (.+?)[\?.]?$",
            r"^do you know (?:about|what|who|how) (.+?)[\?.]?$",
            r"^(?:i want to know|i'?m curious) (?:about|what) (.+?)[\?.]?$",
            r"^can you explain (.+?)[\?.]?$",
        ]
        for p in patterns:
            m = re.search(p, lower)
            if m:
                return m.group(1).strip().rstrip("?.,!")
        # Last resort: remove question words
        cleaned = re.sub(r"^(what|who|how|when|where|why|explain|describe|define|tell me about|can you)\s+", "", lower)
        return cleaned.rstrip("?.,!").strip()

    # ─────────────────────────────────────────────────────────────────────────
    #  CANNED RESPONSES
    # ─────────────────────────────────────────────────────────────────────────
    def _identity(self) -> str:
        stats = self.memory.stats()
        n = f" And you're {self.user_name}!" if self.user_name else ""
        return (
            f"I'm Jarvis — your self-learning personal assistant.{n}\n\n"
            f"Here's what makes me different:\n"
            f"  I crawl the internet 24/7 and learn from real pages\n"
            f"  Right now I know {stats['total_facts']} facts from {stats['urls_visited']} sources\n"
            f"  I use TF-IDF matching to find the most relevant answer for any question\n"
            f"  No AI API — all intelligence comes from what I've actually read\n"
            f"  The longer I run, the smarter and more accurate I become\n\n"
            f"What would you like to talk about?"
        )

    def _help(self) -> str:
        return (
            "Here's everything I can do:\n\n"
            "JUST TALK TO ME:\n"
            "  Say anything naturally. I'll do my best to understand.\n"
            "  I remember our conversation, so 'tell me more', 'why?',\n"
            "  and 'give me an example' all work based on what we discussed.\n\n"
            "ASK QUESTIONS:\n"
            "  'What is machine learning?'\n"
            "  'Who invented the internet?'\n"
            "  'How does photosynthesis work?'\n"
            "  'When did World War 2 end?'\n\n"
            "TEACH ME:\n"
            "  'Learn about black holes'\n"
            "  'Study cybersecurity'\n"
            "  'Research the Roman Empire'\n\n"
            "SEARCH THE WEB:\n"
            "  'Search for Python tutorials'\n\n"
            "DESKTOP CONTROL:\n"
            "  'Open notepad'  |  'Screenshot'\n"
            "  'Type hello'    |  'Press ctrl+s'\n\n"
            "OTHER:\n"
            "  'Status'         - how much I've learned\n"
            "  'Tell me a joke' - yes I know jokes!\n"
            "  'How are you?'   - I have feelings too\n"
            "  'quit'           - exit\n"
        )

    def reset(self):
        self.history.clear()
        self.last_topic = None
        self.last_answer = None
        self.last_results = []


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _extract_quoted(text: str) -> str:
    m = re.search(r'["\'](.+?)["\']', text)
    return m.group(1) if m else ""

def _extract_url(text: str) -> str:
    m = re.search(r'https?://\S+', text)
    return m.group(0) if m else ""

def _extract_hotkey(text: str) -> list:
    m = re.search(r'(ctrl|alt|shift)\+(\w+)', text)
    if m:
        return [m.group(1), m.group(2)]
    m = re.search(r'(?:press|hit)\s+(\w+)', text)
    if m:
        return [m.group(1)]
    return ["enter"]
