# Material Crawling & Repository Module - Implementation Plan

## 📋 Overview
This document outlines the implementation plan for the Material Crawling & Repository module for the AI-powered LMS system.

## 🗄️ Database Models (✅ COMPLETED)
- ✅ `Material` - Stores crawled materials with embeddings
- ✅ `MaterialTopic` - Maps materials to course weeks with approval status
- ✅ `CrawlLog` - Tracks crawler runs

## 📝 Implementation Status

### Phase 1: Core Infrastructure ✅
- [x] Database models (Material, MaterialTopic, CrawlLog)
- [x] Updated requirements.txt with dependencies
- [ ] Pydantic schemas
- [ ] Base crawler class
- [ ] Crawler manager

### Phase 2: Individual Crawlers
- [ ] OER Crawler (PDF/PPT from MIT OCW, NPTEL, etc.)
- [ ] YouTube Crawler (API + transcripts)
- [ ] GitHub Metadata Crawler
- [ ] Blog/Tutorial Crawler
- [ ] ArXiv Article Crawler
- [ ] Dataset Metadata Crawler
- [ ] Coding Exercise Metadata Crawler

### Phase 3: Processing Pipeline
- [ ] Metadata Normalizer
- [ ] Embedding Generator (OpenAI or SentenceTransformers)
- [ ] Quality Scoring Engine
- [ ] Deduplication Engine

### Phase 4: API Endpoints
- [ ] POST /materials/crawl - Run all crawlers
- [ ] POST /materials/crawl/{type} - Run specific crawler
- [ ] GET /materials - List materials
- [ ] GET /materials/search - Vector search
- [ ] GET /materials/course/{course}/week/{week}
- [ ] POST /materials/{id}/approve - Approve material for week

### Phase 5: Integration
- [ ] Integration with AI Recommendation System
- [ ] Material matching to course weeks
- [ ] Lecturer approval workflow

## 🔧 Technical Decisions

### Embeddings
- Using JSONB to store embeddings initially (can migrate to pgvector later)
- Supporting both OpenAI embeddings and SentenceTransformers
- Default to SentenceTransformers (free, local)

### Quality Scoring
- Domain authority: Known educational domains get higher scores
- Recency: Recent materials score higher
- Popularity: Based on views/stars/downloads
- Semantic relevance: Based on embedding similarity

### Deduplication
- Content hash (SHA-256)
- Embedding similarity > 0.92 = duplicate
- Only save materials with quality_score > 0.45

## 📦 Dependencies Added
- beautifulsoup4 - HTML parsing
- lxml - HTML/XML parsing
- PyPDF2 - PDF text extraction
- python-pptx - PPT text extraction
- openai - OpenAI embeddings
- sentence-transformers - Local embeddings
- youtube-transcript-api - YouTube transcripts
- arxiv - ArXiv API
- PyGithub - GitHub API
- requests - HTTP requests
- numpy - Array operations

