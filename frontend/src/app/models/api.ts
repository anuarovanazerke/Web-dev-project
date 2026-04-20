export interface SelectOption {
  value: string;
  label: string;
}

export interface AppOptionsResponse {
  skin_types: SelectOption[];
  face_shapes: SelectOption[];
  concerns: SelectOption[];
  categories: SelectOption[];
  allergens: SelectOption[];
}

export interface Product {
  id: number;
  name: string;
  brand: string;
  category: string;
  price: string;
  recommended_for_skin: string;
  concern_focus: string;
  recommended_for_face_shape: string;
  concern_tags: string[];
  face_shape_tags: string[];
  description: string;
  ingredient_summary: string;
  image_url: string;
  is_budget_friendly: boolean;
  ingredients: {
    id: number;
    name: string;
    is_dangerous: boolean;
    is_common_allergen: boolean;
    description: string;
    allergy_note: string;
  }[];
  match_reason?: string;
  match_score?: number;
}

export interface MatchResponse {
  count: number;
  total_price: string;
  remaining_budget: string;
  selected_categories: string[];
  ingredient_hints: string[];
  allergen_filters: string[];
  recommendations: Product[];
}

export interface FaceAnalysisResponse {
  analysis: {
    provider?: string;
    skin_type: string;
    face_shape: string;
    concern: string;
    notes: string;
    metrics: {
      brightness?: number;
      contrast?: number;
      warmth_ratio?: number;
      aspect_ratio?: number;
      confidence?: number;
    };
    ingredient_hints: string[];
  };
  budget: {
    limit: string;
    selected_total: string;
    remaining: string;
  };
  allergen_filters: string[];
  session: {
    id: number;
    uploaded_image: string;
    recommendations: Product[];
  };
}

export interface UserProfileResponse {
  id: number;
  username: string;
  email: string;
  profile: {
    id: number;
    user: number;
    skin_type: string;
    primary_concern: string;
    budget_limit: string | null;
    allergen_preferences: string;
    allergen_tags: string[];
  } | null;
}
