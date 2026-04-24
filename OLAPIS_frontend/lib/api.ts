// API Client for OLAPIS Backend
import type {
  User,
  AuthResponse,
  Paper,
  PaperCard,
  DiscussionPost,
  Comment,
  VoteState,
  PaginatedResponse,
  ExpertiseLevel,
  TechnicalLevel,
  AskAIMessage,
} from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Helper to get auth headers
function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Helper to get session ID for anonymous voting
function getSessionId(): string {
  if (typeof window === "undefined") return ""
  let sessionId = sessionStorage.getItem("session_id")
  if (!sessionId) {
    sessionId = crypto.randomUUID()
    sessionStorage.setItem("session_id", sessionId)
  }
  return sessionId
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    "X-Session-ID": getSessionId(),
    ...getAuthHeaders(),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }

  return response.json()
}

// ============ AUTH ============

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  const response = await fetchAPI<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })
  
  localStorage.setItem("access_token", response.access_token)
  localStorage.setItem("refresh_token", response.refresh_token)
  
  return response
}

export async function signup(
  email: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  const response = await fetchAPI<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  })
  
  localStorage.setItem("access_token", response.access_token)
  localStorage.setItem("refresh_token", response.refresh_token)
  
  return response
}

export async function completeOnboarding(
  interests: string[],
  expertise_level: ExpertiseLevel
): Promise<User> {
  return fetchAPI<User>("/auth/onboarding", {
    method: "POST",
    body: JSON.stringify({ interests, expertise_level }),
  })
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    return await fetchAPI<User>("/auth/me")
  } catch {
    return null
  }
}

export async function logout(): Promise<void> {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

export async function refreshToken(): Promise<AuthResponse> {
  const refreshToken = localStorage.getItem("refresh_token")
  if (!refreshToken) throw new Error("No refresh token")
  
  const response = await fetchAPI<AuthResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  
  localStorage.setItem("access_token", response.access_token)
  localStorage.setItem("refresh_token", response.refresh_token)
  
  return response
}

// ============ PAPERS ============

export async function getPapersFeed(
  cursor?: string
): Promise<PaginatedResponse<PaperCard>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<PaperCard>>(`/papers/feed?${params}`)
}

export async function getPaper(id: string): Promise<Paper> {
  return fetchAPI<Paper>(`/papers/${id}`)
}

export async function votePaper(
  id: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  return fetchAPI<VoteState>(`/papers/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  })
}

export async function removeVotePaper(id: string): Promise<VoteState> {
  return fetchAPI<VoteState>(`/papers/${id}/vote`, {
    method: "DELETE",
  })
}

// ============ DISCUSSION POSTS ============

export async function getDiscussionsFeed(
  cursor?: string
): Promise<PaginatedResponse<DiscussionPost>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<DiscussionPost>>(`/posts/feed?${params}`)
}

export async function getHomeFeed(
  cursor?: string
): Promise<PaginatedResponse<DiscussionPost>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<DiscussionPost>>(`/feed?${params}`)
}

export async function getDiscussionPost(id: string): Promise<DiscussionPost> {
  return fetchAPI<DiscussionPost>(`/posts/${id}`)
}

export async function createPost(data: {
  title: string
  content: string
  tags: string[]
  technical_level: TechnicalLevel
  linked_paper_id?: string
}): Promise<DiscussionPost> {
  return fetchAPI<DiscussionPost>("/posts", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function votePost(
  id: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  return fetchAPI<VoteState>(`/posts/${id}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  })
}

export async function removeVotePost(id: string): Promise<VoteState> {
  return fetchAPI<VoteState>(`/posts/${id}/vote`, {
    method: "DELETE",
  })
}

// ============ COMMENTS ============

export async function getComments(
  postId: string,
  cursor?: string
): Promise<PaginatedResponse<Comment>> {
  const params = new URLSearchParams()
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<Comment>>(`/posts/${postId}/comments?${params}`)
}

export async function createComment(
  postId: string,
  content: string
): Promise<Comment> {
  return fetchAPI<Comment>(`/posts/${postId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  })
}

export async function voteComment(
  commentId: string,
  vote: "upvote" | "downvote"
): Promise<VoteState> {
  return fetchAPI<VoteState>(`/comments/${commentId}/vote`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  })
}

// ============ SEARCH ============

export async function searchPapers(
  query: string,
  tags?: string[],
  cursor?: string
): Promise<PaginatedResponse<PaperCard>> {
  const params = new URLSearchParams()
  params.set("q", query)
  if (tags?.length) params.set("tags", tags.join(","))
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<PaperCard>>(`/search/papers?${params}`)
}

export async function searchPosts(
  query: string,
  tags?: string[],
  cursor?: string
): Promise<PaginatedResponse<DiscussionPost>> {
  const params = new URLSearchParams()
  params.set("q", query)
  if (tags?.length) params.set("tags", tags.join(","))
  if (cursor) params.set("cursor", cursor)
  
  return fetchAPI<PaginatedResponse<DiscussionPost>>(`/search/posts?${params}`)
}

// ============ ASK AI ============

export async function askAI(
  paperId: string,
  messages: AskAIMessage[]
): Promise<AskAIMessage> {
  return fetchAPI<AskAIMessage>(`/papers/${paperId}/ask`, {
    method: "POST",
    body: JSON.stringify({ messages }),
  })
}

// ============ USER SETTINGS ============

export async function updateUserSettings(data: {
  interests?: string[]
  expertise_level?: ExpertiseLevel
}): Promise<User> {
  return fetchAPI<User>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  })
}

// ============ LINKED PAPERS FOR POSTS ============

export async function getLinkedPosts(
  paperId: string
): Promise<DiscussionPost[]> {
  return fetchAPI<DiscussionPost[]>(`/papers/${paperId}/posts`)
}
