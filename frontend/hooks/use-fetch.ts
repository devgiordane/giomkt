"use client"

/**
 * Base data-fetching hook.
 * Lightweight alternative to SWR — add SWR/React Query later if desired.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useFetch(() => api.get('/dashboard/kpis'))
 */

import { useCallback, useEffect, useRef, useState } from "react"

export interface FetchState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useFetch<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): FetchState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const counterRef = useRef(0)

  const run = useCallback(async () => {
    const id = ++counterRef.current
    setLoading(true)
    setError(null)
    try {
      const result = await fetcher()
      if (id === counterRef.current) setData(result)
    } catch (err) {
      if (id === counterRef.current)
        setError(err instanceof Error ? err.message : "Erro desconhecido")
    } finally {
      if (id === counterRef.current) setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  return { data, loading, error, refetch: run }
}

/**
 * Mutation hook — for POST/PUT/DELETE actions.
 *
 * Usage:
 *   const { mutate, loading, error } = useMutation((body) => api.post('/clients', body))
 *   await mutate({ name: 'Acme' })
 */

export interface MutationState<TResult, TArgs> {
  mutate: (args: TArgs) => Promise<TResult>
  loading: boolean
  error: string | null
}

export function useMutation<TResult, TArgs = void>(
  fn: (args: TArgs) => Promise<TResult>,
): MutationState<TResult, TArgs> {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutate = useCallback(
    async (args: TArgs) => {
      setLoading(true)
      setError(null)
      try {
        return await fn(args)
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Erro desconhecido"
        setError(msg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [fn],
  )

  return { mutate, loading, error }
}
