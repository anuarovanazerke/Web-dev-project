import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, timeout } from 'rxjs';

import {
  AppOptionsResponse,
  FaceAnalysisResponse,
  MatchResponse,
  Product,
  UserProfileResponse
} from '../models/api';
import { resolveApiBaseUrl } from '../core/api-base';

@Injectable({
  providedIn: 'root'
})
export class RecommendationService {
  private readonly apiUrl = resolveApiBaseUrl();

  constructor(private http: HttpClient) {}

  getOptions(): Observable<AppOptionsResponse> {
    return this.http.get<AppOptionsResponse>(`${this.apiUrl}/options/`);
  }

  saveProfile(payload: {
    skin_type: string;
    primary_concern: string;
    budget_limit: number;
    allergen_preferences: string[];
  }): Observable<UserProfileResponse['profile']> {
    return this.http.post<UserProfileResponse['profile']>(`${this.apiUrl}/profile/`, payload);
  }

  getProducts(filters?: {
    category?: string;
    skin_type?: string;
    concern?: string;
    allergens?: string[];
  }): Observable<Product[]> {
    let params = new HttpParams();

    if (filters?.category) {
      params = params.set('category', filters.category);
    }
    if (filters?.skin_type) {
      params = params.set('skin_type', filters.skin_type);
    }
    if (filters?.concern) {
      params = params.set('concern', filters.concern);
    }
    if (filters?.allergens?.length) {
      params = params.set('allergens', filters.allergens.join(','));
    }

    return this.http.get<Product[]>(`${this.apiUrl}/products/`, { params });
  }

  getRecommendations(payload: {
    skin_type: string;
    face_shape?: string;
    concern?: string;
    budget: number;
    allergens?: string[];
  }): Observable<MatchResponse> {
    return this.http.post<MatchResponse>(`${this.apiUrl}/match/`, payload);
  }

  analyzeFace(payload: {
    image: File;
    budget: number;
    concern?: string;
    allergens?: string[];
  }): Observable<FaceAnalysisResponse> {
    const formData = new FormData();
    formData.append('image', payload.image);
    formData.append('budget', String(payload.budget));
    if (payload.concern) {
      formData.append('concern', payload.concern);
    }
    for (const allergen of payload.allergens || []) {
      formData.append('allergens', allergen);
    }
    return this.http
      .post<FaceAnalysisResponse>(`${this.apiUrl}/analyze-face/`, formData)
      .pipe(timeout(45000));
  }

  checkIngredients(payload: { ingredients_text: string; allergens: string[] }): Observable<{
    is_safe: boolean;
    dangerous_ingredients: { name: string; danger: string }[];
    allergen_alerts: { allergen: string; label: string; matched_keywords: string[] }[];
  }> {
    return this.http.post<{
      is_safe: boolean;
      dangerous_ingredients: { name: string; danger: string }[];
      allergen_alerts: { allergen: string; label: string; matched_keywords: string[] }[];
    }>(`${this.apiUrl}/check-ingredients/`, payload);
  }
}
