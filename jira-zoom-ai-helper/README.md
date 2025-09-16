# JIRA Zoom AI Helper - Web Interface

Современный веб-интерфейс для автоматизированной обработки встреч Zoom с созданием задач JIRA через AI. Построен на Next.js 14 с использованием React Server Components и Tailwind CSS.

## 🌟 Особенности

- ✅ **Современный UI/UX** - Responsive дизайн с поддержкой темной темы
- ✅ **Обработка Zoom ссылок** - Автоматическое извлечение ID встречи и пароля
- ✅ **AI Workflow Integration** - Интеграция с системой обработки встреч
- ✅ **Статус мониторинг** - Отслеживание прогресса обработки
- ✅ **TypeScript** - Полная типизация для надежности
- ✅ **shadcn/ui** - Современные компоненты UI
- ✅ **Vercel Analytics** - Встроенная аналитика

## 🛠️ Технологический стек

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS 4.1, shadcn/ui components
- **Build**: Turbopack, PostCSS
- **Icons**: Lucide React
- **Analytics**: Vercel Analytics
- **Fonts**: Geist Sans & Mono

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
npm install
# или
pnpm install
# или
yarn install
```

### 2. Запуск в режиме разработки

```bash
npm run dev
# или
pnpm dev
# или
yarn dev
```

Откройте [http://localhost:3000](http://localhost:3000) в браузере.

### 3. Сборка для production

```bash
npm run build
npm start
```

## 📁 Структура проекта

```
jira-zoom-ai-helper/
├── app/                          # Next.js App Router
│   ├── globals.css              # Глобальные стили
│   ├── layout.tsx               # Корневой layout
│   └── page.tsx                 # Главная страница
├── components/                   # React компоненты
│   ├── ui/                      # shadcn/ui компоненты
│   ├── header.tsx               # Шапка сайта
│   ├── hero-section.tsx         # Главная секция
│   ├── feature-highlights.tsx   # Блок функций
│   └── footer.tsx               # Подвал
├── lib/                         # Утилиты
│   └── utils.ts                 # Общие функции
├── hooks/                       # Custom React hooks
├── public/                      # Статические файлы
├── styles/                      # Дополнительные стили
└── tailwind.config.js          # Конфигурация Tailwind
```

## 🎨 Компоненты

### Header (`components/header.tsx`)
Навигационная шапка с логотипом и меню:
- Адаптивное меню для мобильных устройств
- Кнопки входа и регистрации
- Навигация по разделам

### HeroSection (`components/hero-section.tsx`)
Главная секция с формой обработки встреч:
- **Ввод Zoom ссылки** с валидацией
- **Извлечение параметров** встречи (ID, пароль)
- **API интеграция** с workflow системой
- **Индикация прогресса** обработки
- **Обработка ошибок** с информативными сообщениями

### FeatureHighlights (`components/feature-highlights.tsx`)
Блок с описанием возможностей системы:
- Автоматическое создание JIRA задач
- AI-анализ встреч
- Интеграция с различными системами
- Экономия времени

### Footer (`components/footer.tsx`)
Подвал с дополнительной информацией и ссылками.

## 🔧 Основная функциональность

### Обработка Zoom ссылок

```typescript
const extractMeetingDetails = (url: string) => {
  try {
    const urlObj = new URL(url)
    
    // Извлечение meeting ID из пути
    const pathMatch = urlObj.pathname.match(/\/j\/(\d+)/)
    const meeting_id = pathMatch ? pathMatch[1] : null
    
    // Извлечение пароля из query параметра
    const meeting_password = urlObj.searchParams.get("pwd")
    
    return { meeting_id, meeting_password }
  } catch (error) {
    console.error("Invalid URL format:", error)
    return { meeting_id: null, meeting_password: null }
  }
}
```

### API интеграция

```typescript
const response = await fetch("https://hackathon.shai.pro/api/workflows/run", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: "Bearer YOUR_API_TOKEN",
  },
  body: JSON.stringify({
    inputs: {
      meeting_id,
      meeting_password,
    },
    response_mode: "streaming",
  }),
})
```

## 🎯 Конфигурация цветовой схемы

Приложение использует кастомную цветовую схему, оптимизированную для корпоративных приложений:

```css
:root {
  --primary: oklch(0.35 0.08 195);        /* Cyan-800 для основных элементов */
  --secondary: oklch(0.35 0 0);           /* Серый для вторичных элементов */
  --accent: oklch(0.75 0.15 120);         /* Lime green для акцентов */
  --background: oklch(1 0 0);             /* Белый фон */
  --foreground: oklch(0.25 0 0);          /* Темный текст */
}
```

### Поддержка темной темы

```css
.dark {
  --background: oklch(0.145 0 0);         /* Темный фон */
  --foreground: oklch(0.985 0 0);         /* Светлый текст */
  --primary: oklch(0.985 0 0);            /* Инвертированный primary */
  /* ... остальные цвета */
}
```

## 📱 Адаптивный дизайн

Приложение полностью адаптивно и оптимизировано для всех устройств:

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

```tsx
<div className="container mx-auto max-w-4xl relative">
  <div className="text-center space-y-8">
    <h1 className="text-4xl md:text-6xl font-bold text-balance leading-tight">
      Transform Your Meetings with AI-Powered Insights
    </h1>
  </div>
</div>
```

## 🚦 Состояния интерфейса

### Состояния формы
- **Idle** - Готов к вводу
- **Processing** - Обработка запроса
- **Success** - Успешная обработка
- **Error** - Ошибка обработки

```tsx
const [isProcessing, setIsProcessing] = useState(false)
const [result, setResult] = useState<string | null>(null)
const [error, setError] = useState<string | null>(null)
```

### Индикаторы загрузки

```tsx
{isProcessing ? (
  <>
    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-accent-foreground mr-2" />
    Processing Meeting...
  </>
) : (
  <>
    Process Now
    <ArrowRightIcon className="ml-2 h-5 w-5" />
  </>
)}
```

## 🔍 SEO и производительность

### Метаданные
```typescript
export const metadata: Metadata = {
  title: 'AI Meeting Assistant - Automate JIRA Tasks from Zoom',
  description: 'Transform your Zoom meetings into actionable JIRA tasks with AI-powered analysis',
  keywords: 'AI, Zoom, JIRA, meeting automation, task management',
  openGraph: {
    title: 'AI Meeting Assistant',
    description: 'Automate your meeting workflow with AI',
    images: ['/og-image.png'],
  },
}
```

### Оптимизация изображений
```typescript
import Image from 'next/image'

<Image
  src="/hero-image.jpg"
  alt="AI Meeting Processing"
  width={800}
  height={600}
  priority
  className="rounded-lg shadow-lg"
/>
```

## 🧪 Тестирование

### Unit тесты (Jest)
```bash
npm run test
```

### E2E тесты (Playwright)
```bash
npm run test:e2e
```

### Пример теста компонента
```typescript
import { render, screen } from '@testing-library/react'
import { HeroSection } from '@/components/hero-section'

describe('HeroSection', () => {
  it('renders meeting URL input', () => {
    render(<HeroSection />)
    const input = screen.getByPlaceholderText(/zoom meeting link/i)
    expect(input).toBeInTheDocument()
  })
})
```

## 🚀 Развертывание

### Vercel (рекомендуется)
```bash
npm i -g vercel
vercel --prod
```

### Docker
```dockerfile
FROM node:18-alpine AS base

# Dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

### Переменные окружения

```env
# Production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_ANALYTICS_ID=your_analytics_id

# Development  
NEXT_PUBLIC_API_URL=http://localhost:3001
```

## 🔧 Кастомизация

### Добавление новых компонентов shadcn/ui
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add form
npx shadcn-ui@latest add toast
```

### Кастомные цвета Tailwind
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'custom-blue': '#1e40af',
        'custom-green': '#059669',
      }
    }
  }
}
```

### Добавление анимаций
```tsx
import { motion } from 'framer-motion'

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  <FeatureCard />
</motion.div>
```

## 📊 Аналитика и мониторинг

### Vercel Analytics
```tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

### Custom события
```typescript
import { track } from '@vercel/analytics'

const handleMeetingSubmit = () => {
  track('meeting_processed', {
    meeting_id: meetingId,
    success: true
  })
}
```

## 🔒 Безопасность

### Content Security Policy
```javascript
// next.config.js
const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-eval' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data:;
    font-src 'self';
    connect-src 'self' https://api.yourdomain.com;
`

module.exports = {
  async headers() {
    return [{
      source: '/(.*)',
      headers: [
        { key: 'Content-Security-Policy', value: cspHeader.replace(/\n/g, '') }
      ],
    }]
  },
}
```

### Валидация форм с Zod
```typescript
import { z } from 'zod'

const meetingSchema = z.object({
  meetingUrl: z.string().url().refine(
    (url) => url.includes('zoom.us'),
    { message: "Must be a valid Zoom meeting URL" }
  )
})

type MeetingForm = z.infer<typeof meetingSchema>
```

## 🛠️ Инструменты разработки

### ESLint конфигурация
```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    'prefer-const': 'error',
  }
}
```

### Prettier настройки
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

## 📚 Полезные ресурсы

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Patterns](https://reactpatterns.com/)

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи в браузере (F12 → Console)
2. Убедитесь в корректности API endpoints
3. Проверьте переменные окружения
4. Создайте issue в репозитории с подробным описанием

## 📝 TODO

- [ ] Добавить темную тему
- [ ] Интеграция с дополнительными сервисами
- [ ] Улучшение мобильного интерфейса
- [ ] Добавление PWA поддержки
- [ ] Internationalization (i18n)
