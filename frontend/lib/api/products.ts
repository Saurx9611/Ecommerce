import { apiClient } from './client';

export interface Product {
  id: number;
  title: string;
  description: string | null;
  price: number;
  stock: number;
}

export interface CategoriesSummary {
  categories: { id: number; name: string; count: number; stock: number }[];
  total_products: number;
  total_stock: number;
}

export const productsApi = {
  list: async (): Promise<Product[]> => {
    return apiClient.get<Product[]>('/products/');
  },

  get: async (id: number): Promise<Product> => {
    return apiClient.get<Product>(`/products/${id}`);
  },

  getCategoriesSummary: async (): Promise<CategoriesSummary> => {
    return apiClient.get<CategoriesSummary>('/products/categories/summary');
  },

  create: async (data: { title: string; description?: string; price: number; stock: number }): Promise<Product> => {
    return apiClient.post<Product>('/products/', data);
  }
};
