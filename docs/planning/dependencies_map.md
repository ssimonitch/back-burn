# **Dependencies Map - AI Fitness Companion Backend**

This document tracks dependencies between tasks across all sprints to help identify critical paths and potential bottlenecks.

## **Sprint 2: Authentication & Database Schema**

### Internal Dependencies
```
Schema Design (T1)
    ├── Users Table (T2) ──→ Memories Table (T6)
    ├── Plans Table (T3) ──→ Sets Table (T5)
    ├── Exercises Table (T4) ──→ Sets Table (T5)
    └── Documentation (T10)

JWT Flow Design (T7) ──→ JWT Implementation (T8) ──→ Protected Endpoint (T9)
```

### External Dependencies
- **Prerequisite**: Supabase project must exist
- **Prerequisite**: pgvector extension must be enabled
- **Input Needed**: Supabase service role key for JWT validation

## **Sprint 3: Plan Creation**

### Dependencies from Sprint 2
- ✅ Required: Users Table (Sprint 2, Task 2)
- ✅ Required: Plans Table (Sprint 2, Task 3)
- ✅ Required: JWT Validation (Sprint 2, Task 8)

### Will Enable
- Sprint 4: Workout Logging (requires Plans endpoints)
- Sprint 5: Exercise association with plans

## **Sprint 4: Workout Logging**

### Dependencies from Previous Sprints
- ✅ Required: Sets Table (Sprint 2, Task 5)
- ✅ Required: Plans endpoints (Sprint 3)
- ✅ Required: Authentication (Sprint 2, Task 8)

### Will Enable
- Sprint 7: Affinity system (needs workout completion data)

## **Sprint 5: Exercise Library**

### Dependencies from Previous Sprints
- ✅ Required: Exercises Table (Sprint 2, Task 4)
- ✅ Required: Authentication (Sprint 2, Task 8)

### Will Enable
- Enhanced workout planning in frontend
- Exercise recommendations in AI chat

## **Sprint 6: AI - Chat Interface & Semantic Memory**

### Dependencies from Previous Sprints
- ✅ Required: Memories Table with vectors (Sprint 2, Task 6)
- ✅ Required: Users Table (Sprint 2, Task 2)
- ✅ Required: Authentication (Sprint 2, Task 8)

### External Dependencies
- **Required**: Google Gemini API key
- **Required**: Embedding model selection

### Will Enable
- Sprint 7: Affinity context in AI responses

## **Sprint 7: AI - Affinity System**

### Dependencies from Previous Sprints
- ✅ Required: Workout logging (Sprint 4)
- ✅ Required: Chat interface (Sprint 6)
- ✅ Required: Users Table with affinity_score (Sprint 2, Task 2)

### Will Enable
- Personalized AI responses based on user engagement

## **Sprint 8: Final Testing & Security**

### Dependencies from All Previous Sprints
- All endpoints must be implemented
- All database tables must be stable
- AI integration must be functional

### External Dependencies
- **Required**: Production Supabase instance
- **Required**: Production environment variables
- **Required**: Render production configuration

## **Critical Path**

The following sequence represents the minimum path to MVP:

1. **Database Schema** (Sprint 2) - Foundation for all data
2. **Authentication** (Sprint 2) - Security for all endpoints  
3. **Plans CRUD** (Sprint 3) - Core fitness functionality
4. **Workout Logging** (Sprint 4) - User engagement tracking
5. **AI Chat** (Sprint 6) - Differentiating feature
6. **Affinity System** (Sprint 7) - Personalization

## **Parallel Work Opportunities**

Tasks that can be worked on simultaneously:
- Exercise Library (Sprint 5) can progress independently after Sprint 2
- AI prompt design can begin during Sprint 3-4
- Security planning can start early in Sprint 2

## **Blocker Risks**

1. **Supabase Setup**: If delayed, blocks all of Sprint 2
2. **pgvector Issues**: Would block Sprint 6 AI features
3. **Gemini API Access**: Would block Sprint 6-7
4. **Authentication Problems**: Would cascade to all protected endpoints

---

*Last Updated: January 27, 2025*  
*This is a living document - update as dependencies change*