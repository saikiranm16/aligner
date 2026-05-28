import { useTheme } from "../context/theme-context";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="rounded-full border border-slate-300/80 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-900 dark:border-white/15 dark:bg-white/10 dark:text-slate-100 dark:hover:border-white/40"
    >
      {theme === "dark" ? "Light Mode" : "Dark Mode"}
    </button>
  );
}

