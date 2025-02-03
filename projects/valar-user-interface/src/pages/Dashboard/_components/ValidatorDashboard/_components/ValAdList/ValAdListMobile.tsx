import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/shadcn-utils";
import { Cell, flexRender, Row, Table } from "@tanstack/react-table";

import { ValAdListItem } from "./valAdList.utils";

type KeyType = keyof ValAdListItem | "details";

const ValAdListItemMobile = ({ className, row }: { className?: string; row: Row<ValAdListItem> }) => {
  const cells = row.getAllCells().reduce(
    (acc, cell) => {
      acc[cell.column.id as KeyType] = cell;
      return acc;
    },
    {} as Record<KeyType, Cell<ValAdListItem, unknown>>,
  );

  const renderCell = (key: KeyType) => {
    const cell = cells[key];
    return flexRender(cell.column.columnDef.cell, cell.getContext());
  };

  return (
    <div className={cn("rounded-lg bg-background-light p-3 text-xs", className)}>
      <div className="flex justify-between">
        <div className="flex gap-1">
          <span className="text-text-tertiary">Status:</span>
          {renderCell("status")}
        </div>
        <div className="flex gap-1">
          <span className="text-text-tertiary">Valid until:</span>
          {renderCell("validUntil")}
        </div>
      </div>
      <Separator className="my-1 bg-border" />
      <div className="flex items-end justify-between">
        <div className="space-y-1">
          <div>Ad ID: {renderCell("adId")}</div>
          <div>
            <span className="text-text-tertiary">Occupation:</span> {renderCell("occupation")}
          </div>
          <div>
            <span className="text-text-tertiary">Earning (total):</span>
            {renderCell("earnTotal")}
          </div>
          <div>
            <span className="text-text-tertiary">Earning (to claim):</span> {renderCell("earnClaim")}
          </div>
        </div>
        <div>{renderCell("details")}</div>
      </div>
    </div>
  );
};

const ValAdListMobile = ({ table }: { table: Table<any> }) => {
  return (
    <div>
      <div className="flex flex-col gap-3">
        {table.getRowModel().rows.map((row) => (
          <ValAdListItemMobile key={row.id} row={row} />
        ))}
      </div>
    </div>
  );
};

export default ValAdListMobile;
