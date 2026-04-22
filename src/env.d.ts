/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    user?: {
      id: number;
      nom: string;
      role: string;
    };
  }
}
