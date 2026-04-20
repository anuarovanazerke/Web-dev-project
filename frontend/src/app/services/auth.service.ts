import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { Router } from '@angular/router';
import { UserProfileResponse } from '../models/api';
import { resolveApiBaseUrl } from '../core/api-base';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = resolveApiBaseUrl();
  private readonly loggedInSubject = new BehaviorSubject<boolean>(this.hasToken());
  readonly loggedIn$ = this.loggedInSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  login(username: string, password: string): Observable<{ access: string; refresh: string }> {
    return this.http
      .post<{ access: string; refresh: string }>(`${this.apiUrl}/auth/login/`, {
        username,
        password
      })
      .pipe(
        tap((res) => {
          localStorage.setItem('token', res.access);
          localStorage.setItem('refresh', res.refresh);
          this.loggedInSubject.next(true);
        })
      );
  }

  getCurrentUser(): Observable<UserProfileResponse> {
    return this.http.get<UserProfileResponse>(`${this.apiUrl}/auth/me/`);
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('skinProfile');
    this.loggedInSubject.next(false);
    this.router.navigate(['/login']);
  }

  getToken() {
    return localStorage.getItem('token');
  }

  hasToken(): boolean {
    return !!localStorage.getItem('token');
  }

  isLoggedIn(): boolean {
    return this.hasToken();
  }
} 
