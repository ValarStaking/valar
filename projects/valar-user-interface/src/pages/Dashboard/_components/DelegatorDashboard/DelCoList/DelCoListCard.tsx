import { DelegatorQuery } from "@/api/queries/delegator-contracts";
import ColumnDropdown from "@/components/DataTable/ColumnDropdown";
import TableMain from "@/components/DataTable/TableMain";
import TablePagination from "@/components/DataTable/TablePagination";
import TableSearch from "@/components/DataTable/TableSearch";
import DelCoDrawer from "@/components/Drawers/DelCoDrawer/DelCoDrawer";
import IdenticonAvatar from "@/components/Identicon/Identicon";
import ContractStatus from "@/components/Status/ContractStatus";
import { Separator } from "@/components/ui/separator";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { DelegatorContractGlobalState } from "@/interfaces/contracts/DelegatorContract";
import { ellipseAddress } from "@/utils/convert";
import {
  ColumnFiltersState,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useWallet } from "@txnlab/use-wallet-react";
import { useEffect, useState } from "react";

import DelCoListMobile from "./DelCoListMobile";
import { DelCoListItem, getDelCoListItems } from "./delCoList.utils";
import { useDashboardContext } from "@/contexts/DashboardContext";

const columnHelper = createColumnHelper<DelCoListItem>();

const columnVisibility = {
  start: false,
  duration: false,
  warnings: false,
  latestWarning: false,
  totalPrice: false,
  gated: false,
};

const DelCoListCard = () => {
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const { activeAddress } = useWallet();
  const { algorandClient, valAdsMap } = useAppGlobalState();

  const [delCoMap, setDelCoMap] = useState<Map<bigint, DelegatorContractGlobalState> | undefined>(undefined);
  const [tableData, setTableData] = useState<DelCoListItem[]>([]);
  const { delCoRefetch, setDelCoRefetch } = useDashboardContext();

  //Fetching all Delegator Contracts of current account
  useEffect(() => {
    const fetch = async () => {
      if (activeAddress) {
        const res = await DelegatorQuery.fetchDelManagerContracts(algorandClient.client.algod, activeAddress);

        console.log("Delegator Manager's Contracts Map ::", res);
        setDelCoMap(res);
      } else {
        setDelCoMap(undefined);
      }
    };

    fetch();
  }, [activeAddress, delCoRefetch]);

  // Convert Delegator Contracts to table items
  useEffect(() => {
    const fetch = async () => {
      if (delCoMap && valAdsMap) {
        const delCoList = await getDelCoListItems(delCoMap, valAdsMap);
        setTableData(delCoList);
      }
    };

    fetch();
  }, [delCoMap, valAdsMap]);

  const columns = [
    columnHelper.accessor("stakingAddress", {
      header: "Staking address",
      cell: (info) => {
        return (
          <div className="flex w-[189px] items-center gap-2">
            <IdenticonAvatar value={info.getValue()} className="h-5 w-5" /> {ellipseAddress(info.getValue())}
          </div>
        );
      },
      enableHiding: false,
    }),
    columnHelper.accessor("contractId", { header: "Contract ID" }),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => <ContractStatus status={info.getValue()} />,
    }),
    columnHelper.accessor("valName", {
      header: "Node runner name",
      cell: (info) => {
        return <div className="flex w-[182px] items-center gap-2">{ellipseAddress(info.getValue())}</div>;
      },
    }),
    columnHelper.accessor("adId", { header: "Ad ID" }),
    columnHelper.accessor("expiry", { header: "Contract expiry" }),
    columnHelper.accessor("start", { header: "Contract start" }),
    columnHelper.accessor("duration", { header: "Duration" }),
    columnHelper.accessor("warnings", { header: "Warnings" }),
    columnHelper.accessor("latestWarning", { header: "Latest warning" }),
    columnHelper.accessor("totalPrice", { header: "Total price" }),
    columnHelper.accessor("gated", { header: "Gated" }),
    columnHelper.display({
      header: () => null,
      id: "details",
      cell: ({ row }) => (
        <DelCoDrawer delAppId={row.original.contractId} onClose={() => setDelCoRefetch(!delCoRefetch)} />
      ),
      enableHiding: false,
    }),
  ];

  // Define table
  const contractsTable = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),

    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,

    getFilteredRowModel: getFilteredRowModel(),
    onColumnFiltersChange: setColumnFilters,

    getRowCanExpand: () => true,

    state: {
      pagination,
      columnFilters,
    },

    initialState: {
      columnVisibility: columnVisibility,
    },
  });

  return (
    <>
      <div className="rounded-md border-border py-2 lg:border lg:bg-background-light lg:px-2">
        <div className="flex flex-col gap-2">
          <div className="flex flex-col justify-between gap-2 px-1 lg:flex-row lg:items-center">
            <h1 className="font-bold">Your Contracts</h1>
            <div className="flex justify-between gap-1">
              <TableSearch table={contractsTable} searchColumn="contractId" className="max-w-[150px]" />
              <ColumnDropdown className="hidden lg:block" table={contractsTable} />
            </div>
          </div>
          <Separator className="hidden bg-border lg:block" />
          <div className="flex flex-col rounded-lg bg-background lg:bg-transparent">
            <div className="hidden w-full lg:block">
              <TableMain table={contractsTable} />
            </div>
            <div className="lg:hidden">
              <DelCoListMobile table={contractsTable} />
            </div>
            <div className="flex w-full items-center justify-end">
              <TablePagination table={contractsTable} pagination={pagination} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default DelCoListCard;
