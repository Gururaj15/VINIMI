# Vinimi Vision Safety - AI Development Guide

## Project Overview
This is a React-based worker safety monitoring dashboard built with TypeScript, Vite, and shadcn/ui components. The application provides real-time monitoring and AI-powered analysis of workplace safety.

## Key Architecture Patterns

### Component Structure
- Pages are in `src/pages/` - each represents a major route/feature
- Reusable UI components in `src/components/ui/` follow shadcn/ui patterns
- Layout components in `src/components/` handle page structure
- Example: `DashboardLayout.tsx` provides the main app shell with navigation

### UI/UX Conventions
- Use motion.div from Framer Motion for animations (see `Dashboard.tsx`)
- Glass card effect using `glass-card` class with backdrop blur
- Neon glow effects via `neon-glow` class for emphasis
- Consistent use of gradient text via `bg-gradient-to-r` and `bg-clip-text`

### Data Management
- Authentication state stored in localStorage with key `vinimi_auth`
- Mock data currently used for stats and alerts (to be replaced with API)
- Use react-query for API data fetching when implementing endpoints

## Development Workflow

### Setup & Running
```bash
npm install  # Install dependencies
npm run dev  # Start development server
npm run build  # Production build
npm run preview  # Preview production build
```

### Component Development
1. Use shadcn/ui components from `@/components/ui/`
2. Follow existing patterns for glass-morphism and animations
3. Implement responsive layouts using Tailwind's grid/flex utilities
4. Add motion effects consistent with existing animations

### State Management
- Use React hooks for local state
- Leverage context for auth/theme (see `src/hooks/`)
- Follow patterns in `Workers.tsx` and `LiveMonitoring.tsx` for data fetching

### Styling
- Use Tailwind classes following existing component patterns
- Custom effects (glass, neon) are in global CSS
- Follow existing color scheme using primary/secondary/accent variables

## Common Patterns

### Card Components
```tsx
<Card className="glass-card hover-lift border-white/10">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

### Navigation
```tsx
<Link to={path}>
  <Button variant="ghost" className="w-full justify-start">
    <Icon className="h-4 w-4 mr-2" />
    {label}
  </Button>
</Link>
```

### Animation Structure
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: 0.2 }}
>
  {/* Content */}
</motion.div>
```

## Integration Points
- Authentication via `localStorage.getItem("vinimi_auth")`
- Live video monitoring in `/live-monitoring`
- VLM (Vision Language Model) integration in `/ask-vlm`
- Worker data management in `/workers`