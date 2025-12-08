import { ChangeDetectionStrategy, Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
})
export class LoginComponent {
  @Output() loginSuccess = new EventEmitter<void>();

  isSubmitting = signal(false);
  hasError = signal(false);

  login(): void {
    this.isSubmitting.set(true);
    this.hasError.set(false);

    // Simulate API call
    setTimeout(() => {
      // Simulate a failed login attempt for demonstration
      if (Math.random() > 0.5) {
        this.loginSuccess.emit();
      } else {
        this.hasError.set(true);
      }
      this.isSubmitting.set(false);
    }, 1500);
  }
}
