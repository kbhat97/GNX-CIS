import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LoginComponent, DashboardComponent],
})
export class AppComponent {
  isLoggedIn = signal(false);

  handleLoginSuccess(): void {
    this.isLoggedIn.set(true);
  }

  handleLogout(): void {
    this.isLoggedIn.set(false);
  }
}
