# Client

A Next.js web application built with modern technologies.

## Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | Next.js 16.2.4 |
| **Language** | TypeScript |
| **UI Library** | React 19.2.4 |
| **CSS** | Tailwind CSS 4 |
| **Linting** | Biome 2.2.0 |
| **Formatting** | Biome |

## Project Structure

```
client/
├── public/                  # Static assets (favicons, images, etc.)
├── src/
│   └── app/                 # Next.js App Router
│       ├── about/          # About page route
│       │   └── page.tsx   # About page component
│       ├── globals.css    # Global styles and Tailwind imports
│       ├── layout.tsx     # Root layout component
│       └── page.tsx       # Home page component
├── biome.json              # Biome linter/formatter configuration
├── next.config.ts          # Next.js configuration
├── package.json            # Project dependencies
├── postcss.config.mjs      # PostCSS configuration for Tailwind
├── tsconfig.json           # TypeScript configuration
└── README.md               # Project documentation
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm run start
```

### Lint Code

```bash
npm run lint
```

### Format Code

```bash
npm run format
```

## CSS

This project uses **Tailwind CSS v4** for styling. The configuration is handled through CSS variables in `src/app/globals.css`.

### Tailwind Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## Pages

### Home Page (`/`)

Located at `src/app/page.tsx`

**Features:**
- Hero section with welcome message and call-to-action buttons
- Features section showcasing key benefits
- Fully responsive design with dark mode support
- Tailwind CSS styling

**Components:**
- `HeroSection` - Welcome banner with navigation links
- `FeaturesSection` - Grid display of app features

### About Page (`/about`)

Located at `src/app/about/page.tsx`

**Features:**
- About us heading and description
- Mission statement section
- Back to Home navigation button
- Fully responsive design with dark mode support
- [Tailwind v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide)