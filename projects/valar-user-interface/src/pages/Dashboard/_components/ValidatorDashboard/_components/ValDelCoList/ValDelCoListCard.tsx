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
import { useDashboardContext } from "@/contexts/DashboardContext";
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

import { getValDelCoList, ValDelCoListItem } from "./valDelCoList.utils";
import ValContractListMobile from "./ValDelCoListMobile";

const columnHelper = createColumnHelper<ValDelCoListItem>();

const ValDelCoListCard = () => {
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const { activeAddress } = useWallet();
  const { algorandClient, valAdsMap, valsMap } = useAppGlobalState();

  const [delCoMap, setDelCoMap] = useState<Map<bigint, DelegatorContractGlobalState> | undefined>(undefined);
  const [tableData, setTableData] = useState<ValDelCoListItem[]>([]);
  const { delCoRefetch, setDelCoRefetch } = useDashboardContext();

  //Fetching all Delegator Contracts of under all Validator Ads of current account
  useEffect(() => {
    const fetch = async () => {
      if (activeAddress && valsMap && valAdsMap) {
        // Get all Ad IDs of current account
        const adIds = valsMap.get(activeAddress);
        if (adIds) {
          // Get global state for all Ad IDs of current account
          const adsGS = adIds!.map((adId) => valAdsMap.get(adId));
          // Fetch global state of all active delegator contracts of all Ads of current account
          const contractIds = adsGS.flatMap((ad) => ad!.delAppList.filter((id) => id != 0n));

          const res = await DelegatorQuery.fetchDelegatorContracts(algorandClient.client.algod, contractIds);

          console.log("Delegator Contracts Map ::", res);
          setDelCoMap(res);
        } else {
          // In case the address is not validator owner
          setDelCoMap(undefined);
        }
      } else {
        setDelCoMap(undefined);
      }
    };

    fetch();
  }, [activeAddress, valsMap, valAdsMap, delCoRefetch]);

  // Convert Delegator Contracts to table items
  useEffect(() => {
    const fetch = async () => {
      if (delCoMap) {
        const valDelCoList = await getValDelCoList(delCoMap);
        setTableData(valDelCoList);
      }
    };

    fetch();
  }, [delCoMap]);

  // Define table columns
  const columns = [
    columnHelper.accessor("adId", { header: "Ad ID" }),
    columnHelper.accessor("stakingAddress", {
      header: "Contract for address",
      cell: (info) => {
        return (
          <div className="flex items-center gap-2">
            <IdenticonAvatar value={info.getValue()} className="h-5 w-5" /> {ellipseAddress(info.getValue())}
          </div>
        );
      },
    }),
    columnHelper.accessor("contractId", { header: "Contract ID" }),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => {
        const status = info.getValue();
        return <ContractStatus status={status} />;
      },
    }),
    columnHelper.accessor("validUntil", { header: "Valid until" }),
    columnHelper.accessor("maxStake", { header: "Max stake" }),
    columnHelper.accessor("duration", { header: "Duration" }),
    columnHelper.accessor("currency", { header: "Currency" }),
    columnHelper.accessor("setupFee", { header: "Setup fee" }),
    columnHelper.accessor("opFee", { header: "Op. fee" }),
    columnHelper.accessor("warnings", { header: "Warnings" }),
    columnHelper.accessor("latestWarning", { header: "Latest warning" }),
    columnHelper.accessor("setupTime", { header: "Setup time" }),
    columnHelper.accessor("confirmationTime", { header: "Confirmation time" }),
    columnHelper.accessor("gated", { header: "Gated" }),
    columnHelper.display({
      header: () => null,
      id: "details",
      cell: (info) => (
        <DelCoDrawer delAppId={info.row.getValue("contractId")} onClose={() => setDelCoRefetch(!delCoRefetch)} />
      ),
      enableHiding: false,
    }),
  ];
  const columnVisibility = {
    maxStake: false,
    duration: false,
    currency: false,
    setupFee: false,
    opFee: false,
    warnings: false,
    latestWarning: false,
    setupTime: false,
    confirmationTime: false,
    gated: false,
  };

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
            <h1 className="font-bold">Users' Contracts</h1>
            <div className="flex justify-between gap-1">
              <TableSearch table={contractsTable} searchColumn="adId" className="max-w-[150px]" />
              <ColumnDropdown className="hidden lg:block" table={contractsTable} />
            </div>
          </div>
          <Separator className="hidden bg-border lg:block" />
          <div className="flex flex-col rounded-lg bg-background p-1 lg:bg-transparent">
            <div className="hidden w-full lg:block">
              <TableMain table={contractsTable} />
            </div>
            <div className="lg:hidden">
              <ValContractListMobile table={contractsTable} />
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

export default ValDelCoListCard;
