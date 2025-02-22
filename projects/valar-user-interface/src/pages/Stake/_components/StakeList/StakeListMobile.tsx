import Avatar from "@/components/Avatar/Avatar";
import ValTooltip from "@/components/Tooltip/ValTooltip";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/shadcn-utils";
import { ellipseAddress } from "@/utils/convert";
import { getNfdProfileUrl } from "@/utils/nfd";
import { Cell, flexRender, Row, Table } from "@tanstack/react-table";

import { StakeListItem } from "./stakeList.utils";

type KeyType = keyof StakeListItem | "stake";

const StakeListItemMobile = ({ className, row }: { className?: string; row: Row<StakeListItem> }) => {
  const cells = row.getAllCells().reduce(
    (acc, cell) => {
      acc[cell.column.id as KeyType] = cell;
      return acc;
    },
    {} as Record<KeyType, Cell<StakeListItem, unknown>>,
  );

  const renderCell = (key: KeyType) => {
    const cell = cells[key];
    return flexRender(cell.column.columnDef.cell, cell.getContext());
  };

  return (
    <div className={cn("rounded-lg bg-background-light p-3", className)}>
      <div className="flex items-center justify-between">
        <div>
          <div className="flex gap-1">
            <div className="text-sm">Node Runner:</div>
            <div className="text-sm text-secondary">{ellipseAddress(cells.name.getValue() as string)}</div>
          </div>
          {row.original.nfd && (
            <div className="flex gap-1">
              <div className="text-sm">More Info:</div>
              <LinkExt
                href={getNfdProfileUrl(row.original.nfd.name)}
                children={row.original.nfd.name}
                className={"text-sm text-secondary"}
              />
            </div>
          )}
          <div className="flex gap-1">
            <div className="text-sm">Ad Id:</div>
            <div className="text-sm text-secondary">{renderCell("adId")}</div>
            <ValTooltip relation={row.original.nodeRelation} className="ml-2" />
          </div>
        </div>
        <div>
          <Avatar address={row.original.name} nfd={row.original.nfd} className="h-10 w-10" />
        </div>
      </div>
      <Separator className="mb-3 mt-2 bg-border" />
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm text-text-tertiary">Total Price:</div>
          <div className="">{renderCell("totalPrice")}</div>
        </div>
        <div>
          <div className="text-sm text-text-tertiary">Occupation:</div>
          <div>{renderCell("occupation")}</div>
        </div>
        <div className="">{renderCell("stake")}</div>
      </div>
    </div>
  );
};

const StakeListMobile = ({ table }: { table: Table<any> }) => {
  return (
    <div>
      <div className="flex flex-col gap-3">
        {table.getRowModel().rows.map((row) => (
          <StakeListItemMobile key={row.id} row={row} />
        ))}
      </div>
    </div>
  );
};

export default StakeListMobile;
