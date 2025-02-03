import { cn } from "@/lib/shadcn-utils";
import { Table as ReactTable } from "@tanstack/table-core";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";

const TablePagination = ({
  table,
  pagination,
}: {
  table: ReactTable<any>;
  pagination: {
    pageIndex: number;
    pageSize: number;
  };
}) => {
  const visibleRows = table.getRowModel().rows.length;
  const totalRows = table.options.data.length;
  const [itemStart, setItemStart] = useState<number>(0);
  const [itemEnd, setItemEnd] = useState<number>(0);

  useEffect(() => {
    setItemStart(() => pagination.pageIndex * pagination.pageSize + 1);

    setItemEnd(() => pagination.pageIndex * pagination.pageSize + visibleRows);
  }, [pagination]);

  return (
    <div className="mt-4 flex items-center gap-2">
      <div className="text-sm">
        {itemStart}-{itemEnd} of {totalRows}
      </div>
      <div className="flex gap-2">
        <ChevronLeft
          className={cn("cursor-pointer", !table.getCanPreviousPage() && "opacity-50")}
          onClick={() => table.getCanPreviousPage() && table.previousPage()}
        />

        <ChevronRight
          className={cn("cursor-pointer", !table.getCanNextPage() && "opacity-50")}
          onClick={() => table.getCanNextPage() && table.nextPage()}
        />
      </div>
    </div>
  );
};

export default TablePagination;
