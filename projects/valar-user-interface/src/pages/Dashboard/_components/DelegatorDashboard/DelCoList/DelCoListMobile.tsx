import IdenticonAvatar from "@/components/Identicon/Identicon";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/shadcn-utils";
import { Cell, flexRender, Row, Table } from "@tanstack/react-table";
import { DelCoListItem } from "./delCoList.utils";
import { ellipseAddress } from "@/utils/convert";

type KeyType = keyof DelCoListItem | "details";

const DelCoListItemMobile = ({
  className,
  row,
}: {
  className?: string;
  row: Row<DelCoListItem>;
}) => {
  const cells = row.getAllCells().reduce(
    (acc, cell) => {
      acc[cell.column.id as KeyType] = cell;
      return acc;
    },
    {} as Record<KeyType, Cell<DelCoListItem, unknown>>,
  );

  const renderCell = (key: KeyType) => {
    const cell = cells[key];
    return flexRender(cell.column.columnDef.cell, cell.getContext());
  };

  return (
    <div
      className={cn("rounded-lg bg-background-light p-3 text-xs", className)}
    >
      <div className="flex justify-between">
        <div className="space-y-1">
          <div className="flex gap-1">
            <span className="text-text-tertiary">Status:</span>
            {renderCell("status")}
          </div>
          <div className="flex gap-1">
            <span className="text-text-tertiary">Contract expiry:</span>
            {renderCell("expiry")}
          </div>
        </div>
        <div>
          <IdenticonAvatar value={cells.stakingAddress.getValue() as string} />
        </div>
      </div>
      <Separator className="my-1 bg-border" />
      <div className="flex items-end justify-between">
        <div className="space-y-1">
          <div className="flex gap-1">
            <span className="text-text-tertiary">Staking address:</span>
            {ellipseAddress(cells.stakingAddress.getValue() as string)}
          </div>
          <div className="flex gap-1">
            <span className="text-text-tertiary">Contract ID:</span>
            {renderCell("contractId")}
          </div>
          <div className="flex gap-1">
            <span className="text-text-tertiary">Node runner name:</span>
            {renderCell('valName')}
          </div>
          <div className="flex gap-1">
            <span className="text-text-tertiary">Ad ID:</span>
            {renderCell("adId")}
          </div>
        </div>
        <div>{renderCell("details")}</div>
      </div>
    </div>
  );
};

const DelCoListMobile = ({ table }: { table: Table<any> }) => {
  return (
    <div>
      <div className="flex flex-col gap-3 p-1">
        {table.getRowModel().rows.map((row) => (
          <DelCoListItemMobile key={row.id} row={row} />
        ))}
      </div>
    </div>
  );
};

export default DelCoListMobile;
