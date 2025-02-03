import Avatar from "@/components/Avatar/Avatar";
import ColumnDropdown from "@/components/DataTable/ColumnDropdown";
import TableMain from "@/components/DataTable/TableMain";
import TablePagination from "@/components/DataTable/TablePagination";
import TableSearch from "@/components/DataTable/TableSearch";
import DelCoDrawer from "@/components/Drawers/DelCoDrawer/DelCoDrawer";
import AdStatus from "@/components/Status/AdStatus";
import ITooltip from "@/components/Tooltip/ITooltip";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import LinkExt from "@/components/ui/link-ext";
import { Separator } from "@/components/ui/separator";
import { ROLE_VAL_STR } from "@/constants/smart-contracts";
import { ToolTips } from "@/constants/tooltips";
import { useAppGlobalState } from "@/contexts/AppGlobalStateContext";
import { StakeReqs } from "@/lib/types";
import useUserStore from "@/store/userStore";
import { bytesToStr, ellipseAddress } from "@/utils/convert";
import { getNfdProfileUrl } from "@/utils/nfd";
import {
  ColumnFiltersState,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { getStakeList, StakeListItem } from "./stakeList.utils";
import StakeListMobile from "./StakeListMobile";

const columnHelper = createColumnHelper<StakeListItem>();

function StakeListCard({ stakeReqs }: { stakeReqs: StakeReqs }) {
  const [searchParams] = useSearchParams();
  const nodeRunnerParam = searchParams.get("nodeRunner") ?? searchParams.get("node_runner");

  const { valAdsMap, valNfdsMap } = useAppGlobalState();
  const { user } = useUserStore();
  const [tableData, setTableData] = useState<StakeListItem[]>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [isStakablePresent, setIsStakablePresent] = useState<boolean>(true);
  const [mount, setMount] = useState<boolean>(true);
  const [loadingList, setLoadingList] = useState<boolean>(true);

  const [showAll, setShowAll] = useState<boolean>(() => {
    //True: if Validator
    return (user?.userInfo?.role && bytesToStr(user?.userInfo?.role) === ROLE_VAL_STR) as boolean;
  });

  /**
   * =====================================
   *            Table Column
   * =====================================
   */
  const columns = useMemo(
    () => [
      columnHelper.accessor("name", {
        header: "Node runner name",
        cell: (info) => {
          const nfd = info.row.original.nfd;
          return (
            <div className="flex items-center gap-3">
              <Avatar address={info.getValue()} nfd={nfd} className="h-10 w-10" />
              <div className="flex flex-col gap-1">
                {nfd && (
                  <LinkExt href={getNfdProfileUrl(nfd.name)} children={nfd.name} className={"text-sm text-secondary"} />
                )}
                <p className="text-sm">{ellipseAddress(info.getValue())}</p>
              </div>
            </div>
          );
        },
        enableHiding: false,
        filterFn: (row, columnId, filterValue) => {
          if (columnId !== "name") return false;
          const name = row.original.name.toLowerCase() || "";
          const nfdName = row.original.nfd?.name.toLowerCase() || "";
          const match = name.includes(filterValue.toLowerCase()) || nfdName.includes(filterValue.toLowerCase());
          console.log("Filter:", name, nfdName, filterValue, match);
          return match;
        },
      }),
      columnHelper.accessor("adId", { header: "Ad ID" }),
      columnHelper.accessor("totalPrice", { header: "Total price" }),
      columnHelper.accessor("currency", { header: "Currency" }),
      columnHelper.accessor("occupation", { header: "Occupation" }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => <AdStatus status={info.getValue()} />,
      }),
      columnHelper.accessor("setupFee", { header: "Setup fee" }),
      columnHelper.accessor("opFee", { header: "Op. fee" }),
      columnHelper.accessor("opFeeMin", { header: "Op. fee min" }),
      columnHelper.accessor("opFeeVar", { header: "Op. fee var" }),
      columnHelper.accessor("setupTime", { header: "Setup time" }),
      columnHelper.accessor("confirmationTime", { header: "Confirmation time" }),
      columnHelper.accessor("minDuration", { header: "Min duration" }),
      columnHelper.accessor("maxDuration", { header: "Max duration" }),
      columnHelper.accessor("validUntil", { header: "Valid until" }),
      columnHelper.accessor("maxStake", { header: "Max stake" }),
      columnHelper.accessor("maxWarnings", { header: "Max warnings" }),
      columnHelper.accessor("gated", { header: "Gated" }),
      columnHelper.display({
        header: () => null,
        id: "stake",
        cell: (info) => (
          <DelCoDrawer
            valAppId={info.row.getValue("adId")}
            stakeReqs={stakeReqs}
            canStake={info.row.original.canStake}
          />
        ),
        enableHiding: false,
      }),
      columnHelper.accessor("canStake", {
        header: undefined,
        enableHiding: false,
      }),
    ],
    [tableData],
  );

  const columnVisibility = useMemo(
    () => ({
      currency: false,
      status: false,
      setupFee: false,
      opFee: false,
      opFeeMin: false,
      opFeeVar: false,
      setupTime: false,
      confirmationTime: false,
      minDuration: false,
      maxDuration: false,
      validUntil: false,
      maxStake: false,
      maxWarnings: false,
      gated: false,
      canStake: false,
    }),
    [],
  );

  // Define table
  const validatorTable = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),

    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,

    getFilteredRowModel: getFilteredRowModel(),
    onColumnFiltersChange: setColumnFilters,
    onSortingChange: setSorting,

    state: {
      pagination,
      columnFilters,
      sorting,
    },

    initialState: {
      columnVisibility: columnVisibility,
    },
  });

  /**
   * =====================================================
   *            Use Effects and Functions
   * =====================================================
   */

  // Convert Validator Ads to table items
  useEffect(() => {
    const fetch = async () => {
      if (!valAdsMap) return;

      setLoadingList(true);
      const stakeList = await getStakeList(valAdsMap, stakeReqs, user, valNfdsMap);

      //Checking if any stakableAd is present or not.
      const isStakablePresent = stakeList.some((item) => item.canStake === true);
      setIsStakablePresent(isStakablePresent);

      //If nodeRunnerParam is present the TableData is Sorted else default.
      setTableData(() => {
        if (nodeRunnerParam) {
          const stakableMatches = [];
          const nonStakableMatches = [];
          const stakableNonMatches = [];
          const nonStakableNonMatches = [];

          for (let item of stakeList) {
            if (item.name === nodeRunnerParam) {
              if (item.canStake) {
                stakableMatches.push(item);
              } else {
                nonStakableMatches.push(item);
              }
            } else {
              if (item.canStake) {
                stakableNonMatches.push(item);
              } else {
                nonStakableNonMatches.push(item);
              }
            }
          }

          //If no stakable match found, set ShowAll=true to show unstakable ads of that node_runner.
          if (stakableMatches.length === 0 && nonStakableMatches.length !== 0) setShowAll(true);

          return [...stakableMatches, ...nonStakableMatches, ...stakableNonMatches, ...nonStakableNonMatches];
        } else {
          setSorting([{ id: "canStake", desc: true }]);
        }

        return stakeList;
      });

      setLoadingList(false);

      console.log("Updating table data due to change in valAdsMap, stakeReqs, user", valAdsMap, stakeReqs, user);
    };

    fetch();
  }, [valAdsMap, stakeReqs, user]);

  /**
   * ==============================================================
   *  This is the main method to decide, whether to showAll or not
   * ==============================================================
   */
  useEffect(() => {
    if (loadingList) return;

    //If nodeRunnerParam and Mounting then no Modification needed.
    if (nodeRunnerParam && mount) return setMount(false);

    if (!user) {
      //User Wallet Not-Connected (all ads are stakable)
      setShowAll(false);
    } else if (user.userInfo?.role && bytesToStr(user?.userInfo?.role) === ROLE_VAL_STR) {
      //User is Validator
      setShowAll(true);
    } else if (!isStakablePresent && mount) {
      /**
       * No-Stakable Ad Present and Mounting.
       * Mounting is included to prevent changing of showAll when adjusting StakeReqs.
       */
      setShowAll(true);
    }

    setMount(false); //Mounting Complete
  }, [loadingList]);

  /**
   * ==============================================================
   *          If the user swtiches account then mounting=true,
   *          so that isStakablePresent logic is applied.
   * ==============================================================
   */
  useEffect(() => setMount(true), [user]);

  /**
   * ==============================================================
   *             Filter Table Items based on ShowAll
   * ==============================================================
   */
  useEffect(() => {
    if (!showAll) {
      validatorTable.getColumn("canStake")?.setFilterValue(true);
    } else {
      validatorTable.getColumn("canStake")?.setFilterValue(null);
    }
  }, [showAll]);

  /**
   * =====================================================
   *                  Component Render
   * =====================================================
   */

  return (
    <>
      <div className="rounded-md px-2 py-2 lg:bg-background-light">
        <div className="flex flex-col gap-2">
          <div className="flex flex-col justify-between gap-2 px-1 lg:flex-row lg:items-center">
            <h1 className="font-bold">Node Runners</h1>
            <div className="flex justify-between gap-1">
              <div className="flex w-[200px] items-center gap-2">
                <Checkbox
                  className="border-border"
                  checked={showAll}
                  onCheckedChange={(v) => setShowAll(v === "indeterminate" ? false : v)}
                />
                <Label className="h-6 text-sm font-normal">
                  Show All <ITooltip value={ToolTips.StakeShowAll} />
                </Label>
              </div>
              <TableSearch table={validatorTable} searchColumn="name" className="max-w-[150px]" />
              <ColumnDropdown className="hidden lg:block" table={validatorTable} />
            </div>
          </div>
          <Separator className="hidden bg-border lg:block" />
          <div className="flex flex-col items-end rounded-lg bg-background p-1 lg:bg-transparent">
            <div className="hidden w-full lg:block">
              <TableMain table={validatorTable} />
            </div>
            <div className="block w-full lg:hidden">
              <StakeListMobile table={validatorTable} />
            </div>
            <TablePagination table={validatorTable} pagination={pagination} />
          </div>
        </div>
      </div>
    </>
  );
}

export default StakeListCard;
