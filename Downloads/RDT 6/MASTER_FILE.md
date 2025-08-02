# MASTER FILE - DIGITAL TWIN SYSTEM
## Definitive Guide for Ramki Digital Twin Development

**⚠️ CRITICAL: This file must NEVER be deleted. Only the user can edit it. This is the single source of truth for all development decisions.**

---

## 🎯 CORE MISSION & PRINCIPLES

### **Primary Objective**
Build a sophisticated digital twin system for **1700 users** who will use this day-in, day-out for their queries. The system must be **insightful, relevant, and actionable** - these are the 3 core principles.

**Success Criteria**: If this doesn't serve the users' purpose, it will be shelved. User satisfaction is paramount.

### **User-Centric Philosophy**
- **User's perspective is the most important**
- **User's feedback is the most important**
- **User should be delighted with the insights**
- **Aim is to be the most insightful/helpful agent, not the smartest**

---

## 🛡️ TRUTH POLICY - MANDATORY COMPLIANCE

### **Core Principle: Absolute Honesty**
This document is mandatory reading before any feature implementation, documentation update, or production deployment.

### **Truth Policy Rules**

#### 1. Functional Assessment Requirements
**Before Any Feature Implementation:**
- [ ] Verify Current State: Document what actually exists vs. what's claimed
- [ ] Test Coverage: Implement comprehensive tests before claiming functionality
- [ ] Performance Metrics: Measure and document real performance, not estimates
- [ ] Dependency Check: Verify all dependencies are actually available and working

**During Implementation:**
- [ ] No Placeholder Functions: Every function must have complete implementation logic
- [ ] Clear TODO Markers: Mark incomplete sections with # TODO: [specific task]
- [ ] Error Handling: Implement proper error handling for all edge cases
- [ ] Logging: Add comprehensive logging for debugging and monitoring

**After Implementation:**
- [ ] Functional Verification: Test every claimed feature with real data
- [ ] Documentation Update: Update README.md and architecture.md with accurate information
- [ ] Performance Validation: Measure and document actual performance metrics
- [ ] Integration Testing: Verify all integrations work with real services

#### 2. Code Quality Standards
**Function Implementation Rules:**
- No Duplicate Files: Never create main.py and real_main.py
- Single Source of Truth: Each functionality should exist in exactly one place
- Consolidation Required: Merge duplicate functionality immediately
- Reference Tracking: Update all imports when moving/renaming files

#### 3. Documentation Standards
**README.md Updates Required:**
- [ ] Feature Status: Clear indication of what works vs. what's planned
- [ ] Performance Metrics: Real measured performance, not estimates
- [ ] Dependencies: Accurate list of working dependencies
- [ ] Limitations: Honest assessment of current limitations
- [ ] Testing Instructions: Actual working test commands

#### 4. Testing Requirements
**Before Claiming Functionality:**
- [ ] Unit Tests: Every function must have passing unit tests
- [ ] Integration Tests: Test all integrations with real services
- [ ] Performance Tests: Measure and document actual performance
- [ ] Error Tests: Test error scenarios and edge cases
- [ ] User Acceptance Tests: Verify functionality from user perspective

#### 5. Performance Claims Validation
**Forbidden Performance Claims:**
- ❌ "20% improvement" without baseline measurement
- ❌ "85% accuracy" without test validation
- ❌ "Production ready" without comprehensive testing
- ❌ "Advanced AI" without actual AI implementation

#### 6. Integration Standards
**Before Claiming Integration:**
- [ ] API Keys: Verify actual API keys work
- [ ] Service Availability: Confirm external services are accessible
- [ ] Authentication: Test authentication flows
- [ ] Data Flow: Verify data flows through the integration
- [ ] Error Handling: Test integration error scenarios

#### 7. Code Review Checklist
**Before Merging Any Code:**
- [ ] No Placeholder Functions: All functions have complete implementation
- [ ] No Duplicate Logic: Single source of truth for each functionality
- [ ] Proper Error Handling: Comprehensive error handling implemented
- [ ] Test Coverage: Adequate test coverage for all new functionality
- [ ] Documentation Updated: README.md and architecture.md updated
- [ ] Performance Claims Validated: All performance claims are tested
- [ ] Integration Status Accurate: Integration claims match reality

#### 8. Production Deployment Standards
**Before Production Deployment:**
- [ ] Functional Verification: All claimed features work in staging
- [ ] Performance Validation: Performance meets documented requirements
- [ ] Error Handling: Comprehensive error handling tested
- [ ] Monitoring: Proper monitoring and alerting in place
- [ ] Documentation: All documentation is accurate and up-to-date
- [ ] Security Review: Security implications assessed and addressed

### **🚨 Violation Consequences**
- **Minor Violations**: Warning, code review required, documentation update
- **Major Violations**: Feature freeze, mandatory review, comprehensive audit
- **Critical Violations**: Production block, code freeze, team review

---

## 🏗️ ARCHITECTURE PRINCIPLES

### **Core Approach: Prompt-Controlled Systems**
- **Semantic search** as primary retrieval method
- **Advanced semantic search** for complex queries
- **Enhanced semantic search** for multi-document analysis
- **Adaptive semantic search** for context-aware responses
- **Intelligent action request handler** for specific tasks
- **Advanced intent & entity recognition** for query understanding

### **No Hard Coding Policy**
- No hard coding / sample templates to be used ever
- Should be prompt controlled, use existing intelligence
- Have more reliance on the KB, processed KB
- The format, structure, content, insights etc are all already derived in the KB
- No need for hallucination

### **Multi-Document Processing**
- **Critical Issue**: Answers coming from only 1 document per query
- **Requirement**: Information from multiple documents to be searched, queried, paraphrased, summarized and presented relevantly
- LLM should take multi document, synthesize properly based on chunking, vector db, embeddings
- Give appropriate answers based on the query

---

## 📋 RESPONSE STRUCTURE REQUIREMENTS

### **Standard Response Format**
1. **Summary**: 3+ lines for better context understanding
2. **Insights**: Bulleted points with explanation of 1+ lines
3. **Key High-Level Discussion Points**: 2+ lines for better context
4. **Sources**: From where the information is extracted
5. **Suggested Actions**: Bulleted points
6. **Follow-up Questions**: Natural conversation nudge

### **Response Length Guidelines**
- **Answers need to be longer, based on the question**
- **Summary**: 3+ lines minimum
- **Insights & High-level Discussion Points**: 2+ lines minimum
- **Suggestions**: 1+ lines minimum
- **Actions**: 1+ lines minimum
- **Technical Guidance**: 1+ lines minimum

### **Formatting Requirements**
- **Call dates should be combined** if answer retrieved from multiple files (e.g., "January 20, 2025; November 4, 2025")
- **Don't include attendees section** - creates unnecessary metadata
- **First letter of words should be capitalized**
- **Sentences should be grammatically correct and insightful**
- **Attendees**: 5 names max, rest in '+show more' (cumulative from all transcripts)

---

## 🎯 QUERY TYPES & HANDLING

### **Query Classification**
1. **Status Queries**: "What is the current status of Optum?"
2. **Update Queries**: "What is the update from Sigma?"
3. **Technical Queries**: "What is the stack this agent is using?"
4. **Action Queries**: "What actions are needed for Optum?"
5. **Insight Queries**: "What are Ramki's thoughts on microservices?"
6. **Comparison Queries**: "Compare Optum vs Sigma progress"
7. **Timeline Queries**: "What is the timeline for Project Mississippi?"
8. **Person Queries**: "How is Abhilash doing with his tasks?"
9. **Project Queries**: "What's happening with Project Mississippi?"
10. **System Queries**: "What is the system architecture?"

### **Action Query Special Handling**
**Meeting Scheduling with Ramki:**
- Acknowledge request
- Tell office hour slots (if available in memory)
- Ask for topic of discussion
- Ask for attendees
- Ask for priority (P0-P5)
- Use Graph connectors to trigger mail to Rukmani (Ramki's EA)

**Jira/Confluence Integration:**
- For Jira tickets: Usually asking for action items on person/topic
- System looks into Jira to find tickets
- Action items should be marked as Jira tickets after every call

---

## 🧠 MEMORY & CONVERSATION MANAGEMENT

### **Follow-up Questions Handling**
- **Very tricky but very important**
- Need to use short-term memory and long-term memory
- If follow-up related to previous topic/person: natural turn conversation & continuation
- If different topic/person: treat as new question
- Users ask for specific details: "elaborate this more", "I want only insights", "I want to understand this better"

### **Multi-Turn Conversations**
- Intent & entity enhancements are key
- Apply feasible context engineering principles
- Feedback loop, follow-up questions help better user experience
- Conversation awareness for natural flow

---

## 📝 QUOTE PROCESSING GUIDELINES

### **Ramki's Quotes Processing**
- **Can be used as part of narrative** to give confidence to user
- **Convey emotion** if possible
- **Should not stop abruptly** - use as part of points
- **Sentences should be complete** - no confusion for user
- **Abruptly used words can be ignored**

### **KB Processing for Quotes**
- **Process KBs to ensure quotes are not there**
- **Understand sentence and rephrase** as advice/insight/instruction/statement given by Ramki
- **Don't need exact quotes** if they don't make sense
- **A few grammatical quotes are fine**, others can be removed
- **Essentially these are insights from calls** which users will read & act on
- **If incoherent sentences**, users won't make sense since they weren't present in call
- **Instead, give insights that help** without words being misplaced/misrepresented

---

## 🔄 MULTI-DOCUMENT SYNTHESIS LOGIC

### **Core Principle**
If there are multiple documents on the same topic:
- **Recent one could be evolved discussion**
- **Assumption**: Follow-on tasks from previous calls could have been done
- **New issues could be discussed**
- **Always healthy to take summary, insights, suggestions, follow-up questions from multiple calls**
- **User will be in better position to understand the topic**

### **Synthesis Requirements**
- **Summary**: 3+ lines for better context understanding
- **Insights & High-level Discussion Points**: 2+ lines for better context
- **Suggestions**: 1+ lines
- **Actions**: 1+ lines
- **Technical Guidance**: 1+ lines

---

## 🛠️ DEVELOPMENT PRACTICES

### **Code Quality Standards**
- **Don't go for shortcuts, simpler methods**
- **If function call wasn't supposed to be there - DELETE IT**
- **Don't bypass function calls & keep enlarging code**
- **Code should be modular & accurate** - do the job perfectly
- **Non-used function calls, overridden function calls, simpler shortcuts** - permanently delete
- **Good coding practice**: Fix issue permanently by eliminating redundant pieces
- **Don't bypass or overcomplicate**
- **When fixing function call, fix it in every doc before moving on**
- **Don't do temporary patch work** in each doc & hope system works

### **Permanent Fixes Only**
- **No temporary patch codes**
- **No praying that platform will work**
- **Do comprehensive correct job**
- **Don't look for issues after system fails**
- **If you've learned how to build system, write correct code**

### **Historical Context**
- **27 different iterations** since June 4th
- **27 versions extracted**
- **All have library/dependency/patch work issues & fail**
- **Memory of expectations, iterations, correct function calls, errors, expected answers, format expected**

---

## 🎯 GOOD ENGINEERING PRACTICES

### **Core Principles**
- **Always create Truth Policy** - for system to tell truth & nothing but truth
- **No hallucination, no false claims, no exaggeration**
- **Give very strict protocol for tool to follow**
- **Start with standard, non-negotiable instructions document**

### **Technical Approaches**
- **Recency control** = metadata + scoring + explicit prompt rules
- **Relevancy** = hybrid retrieval + reranking
- **Learning** = feedback-weighted time decay
- **Prompt Controlled Systems** is the right approach for Digital Twin
- **Responses are as good as the KB** - spend more time on KB refinement
- **Start with Context Engineering, Planning** - prompt template structure & doc
- **Give test queries, sample answers, sample format, definition of good & bad**

### **Query Processing Flow**
```
Query → Intent/Entity Analysis → KB Search → Raw Data Extraction → Refine/Structure → Apply Framework Format → Display
```

---

## 📊 ADVANCED ENGINEERING TECHNIQUES

### **Retrieval & Grounding**
- **Hybrid RAG + RRF (Reciprocal Rank Fusion)**: Fuse BM25 hits + vector hits, then re-rank
- **ColBERT/MaxP Reranker**: Lightweight transformer that re-orders top-K passages
- **"Relevance + Window"**: Inject just enough context to fill relevance budget

### **Prompt & Reasoning Loops**
- **ReAct (Reason + Act)**: LLM thinks → calls tool → observes → repeats
- **Self-Ask / Self-Refine**: Agent poses clarifying sub-questions to itself
- **Chain-of-Density (CoD)**: Summarize but keep "dense" info

### **Tool Orchestration**
- **Toolformer-style Function Calling**: LLM chooses JSON calls automatically
- **Contextual Function Selection**: Embedding similarity picks which skill to call

### **Memory & Long-Context**
- **LM-in-the-Loop Summarization Window**: Summaries regenerated each turn
- **Hierarchical Memory**: Tier-1 short-term (Redis), Tier-2 episodic (Cosmos), Tier-3 semantic KB (vector)

### **Multi-Agent Patterns**
- **Critic-Helper / Debate**: Second model critiques first model's answer
- **MCP / ACP / ANP**: Standard envelopes for agent-to-agent hand-off

### **Evaluation & Guardrails**
- **RAGAS / DeepEval**: Automated QA that scores grounding, relevance, faithfulness
- **Guardrails.ai YAML**: Declarative regex & JSON schema guardrails

### **Latency & Cost Tuning**
- **Speculative Decoding**: Small model drafts, larger model verifies
- **Dynamic Routing**: Classification gate decides GPT-4.1 vs GPT-3.5-turbo based on intent and context

### **Fine-Tuning & Embedding Tips**
- **Contrastive Instruction Tuning**: Fine-tune on positive + negative pairs
- **Instructor XL Embeddings**: Task-aware embeddings outperform text-embedding-3

### **Observability & Ops**
- **Structured Trace Logging**: Store thought, action, obs spans with timing
- **Prompt Versioning**: Hash + tag every prompt change

---

## 📋 TEMPLATE SYSTEM

### **Fill-in-the-Blanks Template Kit**
Every chunk stored with canonical keys:
```json
{
  "insight": "...", // CTO's stated belief / POV
  "suggested_actions": [...], // array of {text, owner, priority, due}
  "context": "...", // 1–2-sentence scene-setter
  "follow_ups": [...], // questions raised but not answered
  "takeaways": [...], // bullet summary
  "jira": [...], // array of {id, status, summary, owner}
  "intent": "STATUS | UPDATE | ...",
  "entities": ["Optum", "Sigma", ...],
  "meeting_date": "2025-07-30",
  "source_id": "Meeting-2025-07-30"
}
```

### **Template Rules**
- **Template Keys** match processed KB schema—map once in code, reuse everywhere
- **Auto-dedupe**: before rendering, `uniq_by([text, owner, due])`
- **Date helpers**: `meeting_date_latest` = max(date) among retrieved chunks
- **Source list**: show at most 3 IDs, with "+ n more" if overflow
- **Fallback**: if required slot empty, print "No recent data found (≤ 90 days)"

---

## 🎯 SUCCESS METRICS

### **Project Success Metrics**
- **100% Truth Score**: All claimed features actually work
- **100% Accuracy Score**: All documentation matches reality
- **100% Implementation Score**: All functions have complete implementation
- **90%+ Test Coverage**: Comprehensive test coverage for all functionality
- **Zero Placeholder Code**: No incomplete or placeholder implementations

### **Team Success Metrics**
- **Zero False Claims**: No exaggerated or unverified claims
- **Complete Implementations**: All functions have full implementation
- **Accurate Documentation**: All documentation reflects reality
- **Comprehensive Testing**: All functionality has adequate test coverage
- **Honest Communication**: All communication is truthful and accurate

---

## 🚨 CRITICAL REMINDERS

### **User-Centric Focus**
- **Built for 1700 users** who will use this day-in, day-out
- **Only purpose**: Make sure it's useful, insightful for users/customers
- **If doesn't serve purpose, it'll be shelved**
- **Insightful, relevance, actionable** - the 3 principles

### **No Hard Coding**
- **No hard coding / sample templates** to be used ever
- **Should be prompt controlled**, use existing intelligence
- **Have more reliance on the KB, processed KB**
- **Format, structure, content, insights** all already derived in KB
- **No need for hallucination**

### **Multi-Document Processing**
- **Critical Issue**: Answers coming from only 1 document per query
- **Requirement**: Information from multiple documents to be searched, queried, paraphrased, summarized and presented relevantly
- **LLM should take multi document**, synthesize properly based on chunking, vector db, embeddings
- **Give appropriate answers based on the query**

### **User Satisfaction Priority**
- **User's query is the most important**
- **User's satisfaction is of highest importance**
- **User should be delighted with the insights**

---

## 📝 IMPLEMENTATION CHECKLIST

### **For Every New Feature:**
- [ ] Read this Master File completely
- [ ] Document current state before implementation
- [ ] Implement complete functionality (no placeholders)
- [ ] Write comprehensive tests
- [ ] Measure and document actual performance
- [ ] Update README.md with accurate information
- [ ] Update architecture.md with accurate component status
- [ ] Verify all claims with real testing
- [ ] Get code review approval
- [ ] Update project truth metrics

### **For Every Documentation Update:**
- [ ] Verify all claims against actual functionality
- [ ] Test all commands and instructions
- [ ] Validate all performance claims
- [ ] Check all integration status claims
- [ ] Update feature status if needed
- [ ] Get review approval for accuracy

---

**Last Updated**: [Current Date]  
**Next Review**: [Monthly Review Date]  
**Version**: 1.0  
**Status**: ACTIVE - MANDATORY COMPLIANCE REQUIRED 