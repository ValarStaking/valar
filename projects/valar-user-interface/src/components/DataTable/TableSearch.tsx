import { Input } from "@/components/ui/input";
import { cn } from "@/lib/shadcn-utils";
import { Table as ReactTable } from "@tanstack/table-core";
import { Search } from "lucide-react";

const TableSearch = ({
  className,
  table,
  searchColumn,
}: {
  className?: string;
  table: ReactTable<any>;
  searchColumn: string;
}) => {
  return (
    <div className="flex max-w-xs items-center rounded-full border border-neutral-500 px-2 lg:border-border">
      <Search className="w-4" />
      <Input
        placeholder="Search"
        value={(table.getColumn(searchColumn)?.getFilterValue() as string) ?? ""}
        onChange={(event) => {
          table.getColumn(searchColumn)?.setFilterValue(event.target.value);
        }}
        className={cn(
          "border-0 placeholder:text-sm placeholder:text-text focus-visible:ring-transparent lg:border-border",
          className,
        )}
      />
    </div>
  );
};

export default TableSearch;
