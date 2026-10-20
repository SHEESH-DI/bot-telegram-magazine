import type { NextConfig } from "next";

const config: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Нет server actions, ISR, next/image и серверных сессий: реплики взаимозаменяемы.
};
export default config;
