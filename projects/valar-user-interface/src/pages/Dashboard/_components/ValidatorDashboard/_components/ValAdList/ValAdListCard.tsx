import { ValidatorQuery } from "@/api/queries/validator-ads";
import ColumnDropdown from "@/components/DataTable/ColumnDropdown";
import TableMain from "@/components/DataTable/TableMain";
import TablePagination from "@/components/DataTable/TablePagination";
import TableSearch from "@/components/DataTable/TableSearch";
import ValAdDrawer from "@/components/Drawers/ValAdDrawer/ValAdDrawer";
import AdStatus from "@/components/Status/AdStatus";
import { Separator } from "@/components/ui/separator";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import useUserStore from "@/store/userStore";
import {
  ColumnFiltersState,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useState } from "react";

import { getValAdList, ValAdListItem } from "./valAdList.utils";
import ValAdListMobile from "./ValAdListMobile";
import { useDashboardContext } from "@/contexts/DashboardContext";

const columnHelper = createColumnHelper<ValAdListItem>();

const ValAdListCard = () => {
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const { user } = useUserStore();
  const { algorandClient } = useAppGlobalState();

  const [valAdMap, setValAdMap] = useState<Map<bigint, ValidatorAdGlobalState> | undefined>(undefined);
  const [tableData, setTableData] = useState<ValAdListItem[]>([]);
  const {valAdRefetch, setValAdRefetch } = useDashboardContext()

  //Fetching Validator Ads of current user
  useEffect(() => {
    const fetch = async () => {
      if (user) {
        console.log("Fetching ads of current validator.");
        const res = await ValidatorQuery.fetchValOwnerAds(algorandClient.client.algod, user?.userInfo!);

        console.log("Validator Owner's Ads Map ::", res);
        setValAdMap(res);

      } else {
        setValAdMap(undefined);
      }
    };

    fetch();
  }, [user, valAdRefetch]);

  // Convert Validator Ads to table items, fetching earnings of each Validator Ad
  useEffect(() => {
    const fetch = async () => {
      if (valAdMap) {
        const valAdList = await getValAdList(algorandClient.client.algod, valAdMap);
        setTableData(valAdList);
      }
    };

    fetch();
  }, [valAdMap]);

  // Define table columns
  const columns = [
    columnHelper.accessor("adId", { header: "Ad ID", enableHiding: false }),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => {
        const status = info.getValue();
        return <AdStatus status={status} />;
      },
    }),
    columnHelper.accessor("validUntil", { header: "Valid until" }),
    columnHelper.accessor("occupation", { header: "Occupation" }),
    columnHelper.accessor("earnTotal", { header: "Earnings (total)" }),
    columnHelper.accessor("earnClaim", { header: "Earnings (to claim)" }),
    columnHelper.accessor("currency", { header: "Currency" }),
    columnHelper.accessor("setupFee", { header: "Setup fee" }),
    columnHelper.accessor("opFeeMin", { header: "Op. fee min" }),
    columnHelper.accessor("opFeeVar", { header: "Op. fee var" }),
    columnHelper.accessor("maxStake", { header: "Max stake" }),
    columnHelper.accessor("gratisStake", { header: "Gratis stake" }),
    columnHelper.accessor("minDuration", { header: "Min duration" }),
    columnHelper.accessor("maxDuration", { header: "Max duration" }),
    columnHelper.accessor("setupTime", { header: "Setup time" }),
    columnHelper.accessor("confirmationTime", { header: "Confirmation time" }),
    columnHelper.accessor("maxWarnings", { header: "Max warnings" }),
    columnHelper.accessor("warningTime", { header: "Warning time" }),
    columnHelper.accessor("gated", { header: "Gated" }),
    columnHelper.display({
      header: () => null,
      id: "details",
      cell: ({ row }) => <ValAdDrawer valAppId={row.original.adId} onClose={()=> setValAdRefetch(!valAdRefetch)}  />,
      enableHiding: false,
    }),
  ];
  const columnVisibility = {
    setupFee: false,
    opFeeMin: false,
    opFeeVar: false,
    maxStake: false,
    gratisStake: false,
    minDuration: false,
    maxDuration: false,
    setupTime: false,
    confirmationTime: false,
    maxWarnings: false,
    warningTime: false,
    gated: false,
  };

  // Define table
  const adsTable = useReactTable({
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
            <h1 className="font-bold">Your Ads</h1>
            <div className="flex justify-between gap-1">
              <TableSearch table={adsTable} searchColumn="adId" className="max-w-[150px]" />
              <ColumnDropdown className="hidden lg:block" table={adsTable} />
            </div>
          </div>
          <Separator className="hidden bg-border lg:block" />
          <div className="flex flex-col rounded-lg bg-background p-1 lg:bg-transparent">
            <div className="hidden w-full lg:block">
              <TableMain table={adsTable} />
            </div>
            <div className="lg:hidden">
              <ValAdListMobile table={adsTable} />
            </div>
            <div className="flex w-full items-center justify-end">
              <TablePagination table={adsTable} pagination={pagination} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ValAdListCard;
