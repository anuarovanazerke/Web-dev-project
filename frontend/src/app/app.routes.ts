import { Routes } from '@angular/router';

import { LoginComponent } from './pages/login/login.component';
import { ProfileComponent } from './pages/profile/profile.component';
import { RecommendationsComponent } from './pages/recommendations/recommendations.component';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'profile', pathMatch: 'full' },

  { path: 'login', component: LoginComponent },

  {
    path: 'profile',
    component: ProfileComponent,
    canActivate: [AuthGuard]
  },

  {
    path: 'recommendations',
    component: RecommendationsComponent,
    canActivate: [AuthGuard]
  }
];
