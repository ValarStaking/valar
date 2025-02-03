import { cn } from "@/lib/shadcn-utils";
import { ReactNode } from "react";
import { UseFormReturn } from "react-hook-form";

import { FormControl, FormField, FormItem, FormMessage } from "../ui/form";
import { Input, InputUnit } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Switch } from "../ui/switch";

export const FormInput = ({
  form,
  className,
  name,
  onChangeEffect,
  ...rest
}: {
  form: UseFormReturn<any>;
  className?: string;
  name: string;
  onChangeEffect?: (e: React.ChangeEvent<HTMLInputElement>) => void;
} & Omit<React.ComponentProps<"input">, "form">) => {
  const { type } = rest;
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem className={cn("", className)}>
          <div className={cn("")}>
            <FormControl>
              <Input
                {...field}
                value={field.value || ""}
                {...rest}
                onChange={(e) => {
                  field.onChange(e);
                  if (onChangeEffect) {
                    onChangeEffect(e);
                  }
                }}
              />
            </FormControl>
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  );
};

export const FormInputUnit = ({
  form,
  className,
  name,
  unit,
  onChangeEffect,
  ...rest
}: {
  className?: string;
  form: UseFormReturn<any>;
  name: string;
  unit: ReactNode;
  onChangeEffect?: (e: React.ChangeEvent<HTMLInputElement>) => void;
} & Omit<React.ComponentProps<"input">, "form">) => {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <div className={cn("", className)}>
            <FormControl>
              <InputUnit
                unit={unit}
                unitClassName="text-xs"
                {...field}
                value={field.value || ""}
                {...rest}
                onChange={(e) => {
                  field.onChange(e);
                  if (onChangeEffect) {
                    onChangeEffect(e);
                  }
                }}
              />
            </FormControl>
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  );
};

export const FormSelect = ({
  form,
  className,
  name,
  options,
  placeholder,
  onValueChangeEffect,
  ...rest
}: {
  className?: string;
  form: UseFormReturn<any>;
  name: string;
  placeholder: string;
  onValueChangeEffect?: (value: string) => void;
  options: { value: string; display: string }[];
} & Omit<React.ComponentProps<"select">, "form">) => {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <Select
            onValueChange={(value) => {
              onValueChangeEffect?.(value);
              field.onChange(value);
            }}
            value={field.value}
            disabled={rest.disabled || field.disabled}
          >
            <FormControl>
              <SelectTrigger>
                <SelectValue placeholder={placeholder} />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {options.map((item, index) => (
                <SelectItem key={index} value={item.value}>
                  {item.display}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormMessage />
        </FormItem>
      )}
    />
  );
};

export const FormDate = ({
  form,
  name,
  placeholder = "Pick a Date",
  ...rest
}: {
  form: UseFormReturn<any>;
  name: string;
  placeholder?: string;
} & Omit<React.ComponentProps<"input">, "form">) => {
  const { disabled, className } = rest;
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem className={cn("", className)}>
          <div className={cn("")}>
            <FormControl>
              <Input className="appearance-none" type="date" disabled={disabled} {...rest} {...field} />
            </FormControl>
            <FormMessage />
          </div>
        </FormItem>
      )}
    />
  );
};

export const FormSwitch = ({
  form,
  className,
  name,
  ...rest
}: {
  form: UseFormReturn<any>;
  className?: string;
  name: string;
} & Omit<React.ComponentProps<"input">, "form">) => {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormControl>
            <Switch
              className={cn("", className)}
              checked={field.value}
              onCheckedChange={field.onChange}
              disabled={rest.disabled || field.disabled}
              defaultChecked={field.value}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
};
