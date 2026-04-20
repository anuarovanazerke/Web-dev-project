import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { resolveApiBaseUrl } from '../core/api-base';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = `${resolveApiBaseUrl()}/auth`;

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login/`, {
      username: email,
      password: password
    });
  }

  logout() {
    localStorage.removeItem('token');
  }

  getToken() {
    return localStorage.getItem('token');
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }
}
