import { ChangeDetectionStrategy, Component, EventEmitter, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SkeletonLoaderComponent } from '../skeleton-loader/skeleton-loader.component';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, SkeletonLoaderComponent],
})
export class DashboardComponent implements OnInit {
  @Output() logout = new EventEmitter<void>();

  isLoading = signal(true);
  
  ngOnInit(): void {
    setTimeout(() => {
      this.isLoading.set(false);
    }, 2500);
  }

  metrics = [
    { title: 'Posts Generated', value: '1,204', change: '+12%', isPositive: true },
    { title: 'Engagement Rate', value: '4.87%', change: '-0.5%', isPositive: false },
    { title: 'Followers Gained', value: '891', change: '+21%', isPositive: true },
    { title: 'API Credits Used', value: '75%', change: '', isPositive: false },
  ];

  posts = [
    { title: 'Exploring the Alps', status: 'Published', imageUrl: 'https://picsum.photos/400/300?random=1' },
    { title: 'The Future of AI', status: 'Published', imageUrl: 'https://picsum.photos/400/300?random=2' },
    { title: 'A Week in Tokyo', status: 'Draft', imageUrl: 'https://picsum.photos/400/300?random=3' },
    { title: 'Mastering Sourdough', status: 'Scheduled', imageUrl: 'https://picsum.photos/400/300?random=4' },
    { title: 'Minimalist Living', status: 'Published', imageUrl: 'https://picsum.photos/400/300?random=5' },
    { title: 'Deep Dive into Rust', status: 'Draft', imageUrl: 'https://picsum.photos/400/300?random=6' },
  ];

  getStatusColor(status: string): string {
    switch (status) {
      case 'Published': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'Draft': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'Scheduled': return 'bg-sky-500/20 text-sky-300 border-sky-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  }
}
