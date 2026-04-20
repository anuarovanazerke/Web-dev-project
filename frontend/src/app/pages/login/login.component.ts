import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'] 
})
export class LoginComponent {
  username = '';
  password = '';
  errorMessage = '';
  loading = false;

  constructor(
    private router: Router,
    private auth: AuthService
  ) {
    if (this.auth.isLoggedIn()) {
      this.router.navigate(['/profile']);
    }
  }

  login() {
    this.errorMessage = '';
    this.loading = true;

    this.auth.login(this.username, this.password).subscribe({
      next: () => {
        this.router.navigate(['/profile']);
      },
      error: () => {
        this.errorMessage = 'Invalid username or password';
        this.loading = false;
      }
    });
  }
} 
