/**
 * Purpose: Prop types shared by the generic UI components.
 * Layer:   web/components/ui
 * Exports: Choice
 */
export interface Choice<V extends string = string> {
  value: V;
  label: string;
  icon?: string;
}
