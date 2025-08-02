# STANDARD INSTRUCTIONS - DIGITAL TWIN SYSTEM

## DEVELOPMENT PHILOSOPHY

### 1. FEATURE-DRIVEN DEVELOPMENT
- **Only implement features that provide actual value**
- **No fancy features for the sake of complexity**
- **Every component must enhance user experience**
- **Avoid over-engineering and premature optimization**

### 2. CODE QUALITY STANDARDS
- **Minimal refactoring** - only change what's necessary
- **Single line changes** when possible instead of full rewrites
- **Incremental improvements** over major overhauls
- **Preserve working functionality** at all costs

### 3. PROMPT-CONTROLLED ARCHITECTURE
- **Semantic search** as primary retrieval method
- **Advanced semantic search** for complex queries
- **Enhanced semantic search** for multi-document analysis
- **Adaptive semantic search** for context-aware responses
- **Intelligent action request handler** for specific tasks
- **Advanced intent & entity recognition** for query understanding

### 4. KNOWLEDGE BASE FIRST APPROACH
- **Spend more time on KB refinement** than response generation
- **Quality KB = Quality responses**
- **Reduce costs through better KB processing**
- **Context engineering** before response engineering

## RESPONSE QUALITY STANDARDS

### 1. USER-CENTRIC RESPONSES
- **Always greet and acknowledge** the user's question
- **Provide insightful, to-the-point answers**
- **Include follow-up questions** to encourage engagement
- **Adapt response length** based on query complexity

### 2. CONTENT ORGANIZATION
- **Summary**: 3+ lines for better context understanding
- **Insights**: 2+ lines for meaningful analysis
- **High-level discussion points**: 2+ lines for comprehensive coverage
- **Suggestions**: 1+ lines for actionable advice
- **Actions**: 1+ lines for clear next steps
- **Technical guidance**: 1+ lines for specific direction

### 3. QUOTE PROCESSING
- **Remove incoherent sentences** and incomplete thoughts
- **Rephrase as insights/advice** when grammatically sound
- **Preserve Ramki's original words** when they add value
- **Convey emotion** without breaking flow
- **Ensure complete sentences** for user understanding

### 4. MULTI-DOCUMENT HANDLING
- **Assume recent documents** contain evolved discussions
- **Synthesize across multiple calls** on same topic
- **Extract summary, insights, action items** from processed KB
- **Avoid date-based extraction** - focus on readability
- **Handle conflicting views** transparently

## TECHNICAL IMPLEMENTATION GUIDELINES

### 1. MEMORY MANAGEMENT
- **Short-term memory** for conversation context
- **Long-term memory** for user preferences and patterns
- **Conversation awareness** for natural follow-ups
- **Topic continuity** for related queries

### 2. SPECIAL FUNCTIONALITY
- **Meeting scheduling** with Ramki's office hours
- **Jira integration** for action items and tickets
- **Priority classification** (P0-P5) for scheduling
- **Attendee management** for meeting coordination

### 3. SEARCH AND RETRIEVAL
- **Recency control** = metadata + scoring + explicit prompt rules
- **Relevancy** = hybrid retrieval + reranking
- **Learning** = feedback-weighted time decay
- **Context-aware** retrieval for multi-turn conversations

## TESTING AND VALIDATION

### 1. SAMPLE QUERIES TO SUPPORT
- General topic questions
- Specific person queries
- Action item requests
- Meeting scheduling requests
- Follow-up questions
- Insight requests
- Technical guidance requests

### 2. RESPONSE FORMATS
- Long responses for comprehensive topics
- Medium responses for specific queries
- Short responses for quick facts
- Structured responses with sections
- Conversational responses with follow-ups

### 3. QUALITY METRICS
- **No hallucination** - all content from KB
- **Grammatical correctness** - every sentence meaningful
- **Logical flow** - coherent narrative
- **Actionable insights** - practical value
- **User engagement** - encourages further questions

## DEPLOYMENT AND SCALING

### 1. MODULAR ARCHITECTURE
- **Independent components** for easy updates
- **Plugin-based system** for new features
- **API-first design** for integration
- **Configuration-driven** behavior

### 2. PERFORMANCE OPTIMIZATION
- **Efficient KB processing** to reduce costs
- **Smart caching** for frequent queries
- **Lazy loading** for large datasets
- **Incremental updates** for KB changes

### 3. MONITORING AND FEEDBACK
- **Response quality tracking**
- **User satisfaction metrics**
- **System performance monitoring**
- **Continuous improvement loop**

---

**These instructions are the foundation for all development decisions.** 