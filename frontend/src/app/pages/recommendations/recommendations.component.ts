import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';

import {
  AppOptionsResponse,
  FaceAnalysisResponse,
  MatchResponse,
  Product
} from '../../models/api';
import { AuthService } from '../../services/auth.service';
import { RecommendationService } from '../../services/recommendation.service';

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recommendations.component.html',
  styleUrl: './recommendations.css'
})
export class RecommendationsComponent implements OnInit {
  profile: { skin_type?: string; concern?: string; budget?: number; allergens?: string[] } = {};
  recommendations: Product[] = [];
  catalog: Product[] = [];
  selectedProduct: Product | null = null;
  errorMessage = '';
  catalogErrorMessage = '';
  loading = true;
  catalogLoading = true;
  options: AppOptionsResponse = {
    skin_types: [],
    face_shapes: [],
    concerns: [],
    categories: [],
    allergens: []
  };
  matchMeta: MatchResponse | null = null;
  faceAnalysis: FaceAnalysisResponse | null = null;
  noticeMessage = '';

  constructor(
    private recommendationService: RecommendationService,
    private auth: AuthService
  ) {}

  ngOnInit() {
    const savedProfile = localStorage.getItem('skinProfile');
    const savedAnalysis = localStorage.getItem('faceAnalysis');
    const notice = localStorage.getItem('analysisNotice');
    this.profile = savedProfile ? JSON.parse(savedProfile) : {};
    this.faceAnalysis = savedAnalysis ? JSON.parse(savedAnalysis) : null;
    this.noticeMessage = notice || '';
    localStorage.removeItem('analysisNotice');

    this.recommendationService.getOptions().subscribe({
      next: (options) => {
        this.options = options;
      }
    });

    this.loadData();
    this.loadCatalog();
  }

  loadData() {
    this.loading = true;
    this.errorMessage = '';
    const requestData = {
      skin_type: this.profile.skin_type || this.faceAnalysis?.analysis.skin_type || 'normal',
      concern: this.profile.concern || this.faceAnalysis?.analysis.concern || '',
      face_shape: this.faceAnalysis?.analysis.face_shape || '',
      budget: this.profile.budget || Number(this.faceAnalysis?.budget.limit) || 10000,
      allergens: this.profile.allergens || []
    };

    this.recommendationService.getRecommendations(requestData).subscribe({
      next: (res) => {
        this.matchMeta = res;
        this.recommendations = res.recommendations;
        this.loading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.errorMessage = this.extractErrorMessage(error, 'Cannot load recommendations.');
        this.loading = false;
      }
    });
  }

  loadCatalog() {
    this.catalogLoading = true;
    this.catalogErrorMessage = '';
    this.recommendationService.getProducts({
      skin_type: this.profile.skin_type || this.faceAnalysis?.analysis.skin_type,
      concern: this.profile.concern || this.faceAnalysis?.analysis.concern,
      allergens: this.profile.allergens || []
    }).subscribe({
      next: (products) => {
        this.catalog = products;
        this.catalogLoading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.catalogErrorMessage = this.extractErrorMessage(error, 'Could not load the skincare catalog.');
        this.catalogLoading = false;
      }
    });
  }

  loadFullCatalog() {
    this.catalogLoading = true;
    this.catalogErrorMessage = '';
    this.recommendationService.getProducts().subscribe({
      next: (products) => {
        this.catalog = products;
        this.catalogLoading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.catalogErrorMessage = this.extractErrorMessage(error, 'Could not load the full skincare catalog.');
        this.catalogLoading = false;
      }
    });
  }

  selectProduct(product: Product) {
    this.selectedProduct = product;
  }

  closeModal() {
    this.selectedProduct = null;
  }

  labelFor(type: 'skin_types' | 'concerns', value?: string) {
    if (!value) {
      return 'Not selected';
    }
    return this.options[type].find((item) => item.value === value)?.label || value;
  }

  logout() {
    this.auth.logout();
  }

  private extractErrorMessage(error: HttpErrorResponse, fallback: string) {
    const details = error.error;
    if (typeof details === 'string' && details.trim()) {
      return details;
    }
    if (details?.detail) {
      return details.detail;
    }
    return fallback;
  }
}
