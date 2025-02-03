import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/shadcn-utils";
import { Table as ReactTable } from "@tanstack/table-core";
import { ChevronDown } from "lucide-react";

const ColumnDropdown = ({ className, table }: { className?: string; table: ReactTable<any> }) => {
  return (
    <div className={cn("", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button className="rounded-full border border-border bg-background-light hover:bg-background">
            Columns <ChevronDown />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="border-0 bg-background text-white">
          <DropdownMenuLabel className="border-b border-border">Columns</DropdownMenuLabel>
          {table
            .getAllColumns()
            .filter((column) => column.getCanHide())
            .map((column) => {
              return (
                <DropdownMenuCheckboxItem
                  key={column.id}
                  className="capitalize"
                  checked={column.getIsVisible()}
                  onCheckedChange={(value) => column.toggleVisibility(!!value)}
                  onSelect={(e) => e.preventDefault()}
                >
                  {column.columnDef.header?.toString()}
                </DropdownMenuCheckboxItem>
              );
            })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default ColumnDropdown;
