import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AppOptionsResponse } from '../../models/api';
import { AuthService } from '../../services/auth.service';
import { RecommendationService } from '../../services/recommendation.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.css'
})
export class ProfileComponent implements OnInit {
  skinType = '';
  skinProblem = '';
  budget = '';
  selectedAllergens: string[] = [];
  imageFile: File | null = null;
  imageName = '';
  loading = false;
  errorMessage = '';
  infoMessage = '';
  analysisStatus = '';
  username = '';
  ingredientText = '';
  ingredientResult: {
    is_safe: boolean;
    dangerous_ingredients: { name: string; danger: string }[];
    allergen_alerts: { allergen: string; label: string; matched_keywords: string[] }[];
  } | null = null;

  options: AppOptionsResponse = {
    skin_types: [
      { value: 'dry', label: 'Dry' },
      { value: 'oily', label: 'Oily' },
      { value: 'combo', label: 'Combination' },
      { value: 'normal', label: 'Normal' }
    ],
    face_shapes: [],
    concerns: [
      { value: 'acne', label: 'Acne' },
      { value: 'rosacea', label: 'Rosacea' },
      { value: 'wrinkles', label: 'Wrinkles' },
      { value: 'pigmentation', label: 'Pigmentation' },
      { value: 'dehydration', label: 'Dehydration' },
      { value: 'sensitivity', label: 'Sensitivity' },
      { value: 'dullness', label: 'Dullness' },
      { value: 'pores', label: 'Visible pores' },
      { value: 'dark_circles', label: 'Dark circles' }
    ],
    categories: [],
    allergens: [
      { value: 'fragrance', label: 'Fragrance / Perfume' },
      { value: 'alcohol', label: 'Alcohol Denat' },
      { value: 'essential_oils', label: 'Essential oils' },
      { value: 'lanolin', label: 'Lanolin' },
      { value: 'formaldehyde', label: 'Formaldehyde releasers' },
      { value: 'sulfates', label: 'Sulfates' }
    ]
  };

  constructor(
    private router: Router,
    private auth: AuthService,
    private recommendationService: RecommendationService
  ) {}

  ngOnInit() {
    this.loadOptions();
    this.auth.getCurrentUser().subscribe({
      next: (user) => {
        this.username = user.username;
      },
      error: () => {
        this.username = '';
      }
    });
  }

  loadOptions() {
    this.recommendationService.getOptions().subscribe({
      next: (options) => {
        this.options = options;
      },
      error: () => {
        this.infoMessage = '';
      }
    });
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] || null;
    this.imageFile = file;
    this.imageName = file?.name || '';
  }

  toggleAllergen(value: string, checked: boolean) {
    if (checked) {
      this.selectedAllergens = [...new Set([...this.selectedAllergens, value])];
      return;
    }
    this.selectedAllergens = this.selectedAllergens.filter((item) => item !== value);
  }

  runIngredientCheck() {
    this.ingredientResult = null;
    this.errorMessage = '';
    if (!this.ingredientText.trim()) {
      return;
    }
    this.recommendationService
      .checkIngredients({
        ingredients_text: this.ingredientText,
        allergens: this.selectedAllergens
      })
      .subscribe({
        next: (result) => {
          this.ingredientResult = result;
        },
        error: (error: HttpErrorResponse) => {
          this.errorMessage = this.extractErrorMessage(error, 'Could not check the ingredient list.');
        }
      });
  }

  submitProfile() {
    this.loading = true;
    this.errorMessage = '';
    this.infoMessage = '';
    this.analysisStatus = 'Preparing your skincare request...';

    const budgetValue = Number(this.budget);
    const hasManualProfile = Boolean(this.skinType && this.skinProblem);
    const hasPhotoAnalysis = Boolean(this.imageFile);

    if (!this.budget.trim() || Number.isNaN(budgetValue) || budgetValue < 0) {
      this.loading = false;
      this.analysisStatus = '';
      this.errorMessage = 'Please enter a valid budget.';
      return;
    }

    if (!hasManualProfile && !hasPhotoAnalysis) {
      this.loading = false;
      this.analysisStatus = '';
      this.errorMessage = 'Choose skin type and concern, or upload a photo.';
      return;
    }

    const profileData = {
      skin_type: this.skinType,
      primary_concern: this.skinProblem,
      budget_limit: budgetValue,
      allergen_preferences: this.selectedAllergens
    };

    const finalizeWithRecommendations = () => {
      const payload = {
        skin_type: this.skinType,
        concern: this.skinProblem,
        budget: budgetValue,
        allergens: this.selectedAllergens
      };

      if (hasManualProfile) {
        localStorage.setItem('skinProfile', JSON.stringify(payload));
      } else {
        localStorage.removeItem('skinProfile');
      }

      if (this.imageFile) {
        this.analysisStatus = 'Uploading photo and waiting for AI analysis... usually under 45 seconds.';
        this.recommendationService
          .analyzeFace({
            image: this.imageFile,
            budget: budgetValue,
            concern: this.skinProblem,
            allergens: this.selectedAllergens
          })
          .subscribe({
            next: (res) => {
              localStorage.setItem('faceAnalysis', JSON.stringify(res));
              this.loading = false;
              this.analysisStatus = '';
              this.router.navigate(['/recommendations']);
            },
            error: (error: HttpErrorResponse) => {
              this.loading = false;
              this.analysisStatus = '';
              localStorage.removeItem('faceAnalysis');
              localStorage.setItem(
                'analysisNotice',
                this.extractErrorMessage(
                  error,
                  'Photo analysis timed out or failed, so recommendations were generated from your manual profile only.'
                )
              );
              this.router.navigate(['/recommendations']);
            }
          });
      } else {
        localStorage.removeItem('faceAnalysis');
        localStorage.removeItem('analysisNotice');
        this.loading = false;
        this.analysisStatus = '';
        this.router.navigate(['/recommendations']);
      }
    };

    if (!hasManualProfile) {
      finalizeWithRecommendations();
      return;
    }

    this.analysisStatus = 'Saving your skincare profile...';
    this.recommendationService.saveProfile(profileData).subscribe({
      next: () => {
        finalizeWithRecommendations();
      },
      error: () => {
        this.loading = false;
        this.analysisStatus = '';
        this.errorMessage = 'Could not save your profile.';
      }
    });
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
