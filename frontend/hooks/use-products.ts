"use client"

import { api } from "@/lib/api"
import type { ProductsResponse, CreateProductBody, UpdateProductBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useProducts(accountId?: number) {
  return useFetch<ProductsResponse>(
    () => api.get("/products", accountId ? { account_id: accountId } : undefined),
    [accountId],
  )
}

export function useCreateProduct() {
  return useMutation((body: CreateProductBody) => api.post<{ id: number }>("/products", body))
}

export function useUpdateProduct(id: number) {
  return useMutation((body: UpdateProductBody) => api.put<{ ok: boolean }>(`/products/${id}`, body))
}

export function useDeleteProduct() {
  return useMutation((id: number) => api.delete(`/products/${id}`))
}
