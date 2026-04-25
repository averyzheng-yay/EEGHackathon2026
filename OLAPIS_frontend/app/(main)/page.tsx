"use client"

import { useEffect, useState, useCallback } from "react"
import useSWRInfinite from "swr/infinite"
import { Plus, RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PostCard } from "@/components/post-card"
import { CreatePostModal } from "@/components/create-post-modal"
import { AskAIModal } from "@/components/ask-ai-modal"
import { useAuthStore } from "@/lib/store"
import { getHomeFeed, votePost, removeVotePost } from "@/lib/api"
import type { DiscussionPost, PaginatedResponse, PaperCard, VoteType } from "@/lib/types"

const PAGE_SIZE = 20

export default function HomePage() {
  const { user } = useAuthStore()
  const [createPostOpen, setCreatePostOpen] = useState(false)
  const [askAIPaper, setAskAIPaper] = useState<PaperCard | null>(null)
  const [userVotes, setUserVotes] = useState<Record<string, VoteType>>({})
  const [voteCounts, setVoteCounts] = useState<Record<string, { upvote_count: number; downvote_count: number }>>({})

  const getKey = (
    pageIndex: number,
    previousPageData: PaginatedResponse<DiscussionPost> | null
  ) => {
    if (previousPageData && !previousPageData.has_more) return null
    if (pageIndex === 0) return "feed-page-0"
    return `feed-page-${pageIndex}-${previousPageData?.cursor}`
  }

  const { data, error, size, setSize, isLoading, isValidating, mutate } = useSWRInfinite(
    getKey,
    async (key) => {
      const cursor = key.includes("-") ? key.split("-").pop() : undefined
      return getHomeFeed(cursor === "0" ? undefined : cursor)
    },
    {
      revalidateFirstPage: false,
      revalidateOnFocus: false,
    }
  )

  const posts = data?.flatMap((page) => page.items) ?? []
  const hasMore = data?.[data.length - 1]?.has_more ?? false
  const isEmpty = data?.[0]?.items.length === 0

  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000 &&
        hasMore &&
        !isValidating
      ) {
        setSize(size + 1)
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [hasMore, isValidating, size, setSize])

  const handleVote = useCallback(
    async (postId: string, vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = userVotes[postId]
      setUserVotes((prev) => ({ ...prev, [postId]: vote }))
      try {
        const result = await votePost(postId, vote)
        setUserVotes((prev) => ({ ...prev, [postId]: result.user_vote }))
        setVoteCounts((prev) => ({ ...prev, [postId]: { upvote_count: result.upvote_count, downvote_count: result.downvote_count } }))
      } catch {
        setUserVotes((prev) => ({ ...prev, [postId]: prevVote }))
        toast.error("Failed to vote")
      }
    },
    [user, userVotes]
  )

  const handleRemoveVote = useCallback(
    async (postId: string) => {
      const prevVote = userVotes[postId]
      setUserVotes((prev) => ({ ...prev, [postId]: null }))
      try {
        const result = await removeVotePost(postId, prevVote!)
        setUserVotes((prev) => ({ ...prev, [postId]: result.user_vote }))
        setVoteCounts((prev) => ({ ...prev, [postId]: { upvote_count: result.upvote_count, downvote_count: result.downvote_count } }))
      } catch {
        setUserVotes((prev) => ({ ...prev, [postId]: prevVote }))
        toast.error("Failed to remove vote")
      }
    },
    [userVotes]
  )

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">For You</h1>
          <p className="text-muted-foreground">
            {user
              ? "Personalized discussions based on your interests"
              : "Top discussions from the community"}
          </p>
        </div>
        {user && (
          <Button onClick={() => setCreatePostOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Post
          </Button>
        )}
      </div>

      {/* Feed */}
      <div className="space-y-4">
        {isLoading ? (
          // Loading skeletons
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="rounded-lg border p-4">
              <div className="flex gap-3">
                <div className="space-y-2">
                  <Skeleton className="h-8 w-8 rounded" />
                  <Skeleton className="h-4 w-6" />
                  <Skeleton className="h-8 w-8 rounded" />
                </div>
                <div className="flex-1 space-y-3">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-6 w-full" />
                  <Skeleton className="h-6 w-3/4" />
                  <div className="flex gap-2">
                    <Skeleton className="h-5 w-16 rounded-full" />
                    <Skeleton className="h-5 w-20 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">Failed to load posts</p>
            <Button variant="outline" onClick={() => mutate()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try again
            </Button>
          </div>
        ) : isEmpty ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No posts yet</p>
            {user && (
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setCreatePostOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create the first post
              </Button>
            )}
          </div>
        ) : (
          <>
            {posts.map((post) => {
              const counts = voteCounts[post.id]
              return <PostCard
                key={post.id}
                post={{ ...post, ...(counts ?? {}) }}
                userVote={userVotes[post.id]}
                onVote={(vote) => handleVote(post.id, vote)}
                onRemoveVote={() => handleRemoveVote(post.id)}
                onAskAI={
                  post.linked_paper
                    ? () => setAskAIPaper(post.linked_paper!)
                    : undefined
                }
              />
            })}

            {/* Loading more indicator */}
            {isValidating && (
              <div className="flex justify-center py-4">
                <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* End of feed */}
            {!hasMore && posts.length > 0 && (
              <p className="text-center text-sm text-muted-foreground py-8">
                {"You've reached the end"}
              </p>
            )}
          </>
        )}
      </div>

      {/* Modals */}
      <CreatePostModal open={createPostOpen} onOpenChange={setCreatePostOpen} />
      {askAIPaper && (
        <AskAIModal
          paper={askAIPaper}
          open={!!askAIPaper}
          onOpenChange={(open) => !open && setAskAIPaper(null)}
        />
      )}
    </div>
  )
}
