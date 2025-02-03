import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { flexRender } from "@tanstack/react-table";
import { Table as ReactTable } from "@tanstack/table-core";
import { ChevronDown, ChevronsUpDown, ChevronUp } from "lucide-react";

import { ScrollArea, ScrollBar } from "../ui/scroll-area";

const TableMain = ({ table }: { table: ReactTable<any> }) => {
  return (
    <>
      <ScrollArea>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow className="border-0 hover:bg-background-light" key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} colSpan={header.colSpan}>
                    <div className="flex flex-nowrap text-nowrap">
                      {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() && !header.column.getIsSorted() && (
                        <ChevronsUpDown
                          className="ml-1 mt-[2px] h-4 w-4 cursor-pointer"
                          onClick={header.column.getToggleSortingHandler()}
                        />
                      )}
                      {
                        {
                          asc: !header.isPlaceholder && (
                            <ChevronUp
                              className="ml-1 mt-[2px] h-4 w-4 cursor-pointer"
                              onClick={header.column.getToggleSortingHandler()}
                            />
                          ),
                          desc: !header.isPlaceholder && (
                            <ChevronDown
                              className="ml-1 mt-[2px] h-4 w-4 cursor-pointer"
                              onClick={header.column.getToggleSortingHandler()}
                            />
                          ),
                        }[header.column.getIsSorted() as string]
                      }
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="text-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </>
  );
};

export default TableMain;
