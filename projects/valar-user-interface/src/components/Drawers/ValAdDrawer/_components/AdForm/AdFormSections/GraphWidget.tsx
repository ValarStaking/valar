import { ValidatorAdConfigGraph } from "@/components/Graphs/ValidatorAdConfigGraph";
import { ChartConfig } from "@/components/ui/chart";
import { adFormSchema } from "@/lib/form-schema";
import { useEffect, useState } from "react";
import { UseFormReturn } from "react-hook-form";
import { z } from "zod";

const chartConfig = {
  x: {
    label: "X",
    color: "hsl(var(--chart-3))",
  },
  y: {
    label: "Y",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

type GraphPointType = { x: number; y: number };

const GraphWidget = ({ form }: { form: UseFormReturn<z.infer<typeof adFormSchema>> }) => {
  const [data, setData] = useState<GraphPointType[]>([{ x: 0, y: 0 }]);

  useEffect(() => {
    const currentValues = form.getValues();
    const operationFeeMin = currentValues.minOperationalFee;
    const operationFeeVar = currentValues.varOperationalFee;
    const stakeMax = currentValues.maxStake;

    const maxVarFee = (operationFeeVar * stakeMax) / 10 ** 5;
    const P1 = { x: 0, y: operationFeeMin };
    const P2 = {
      x: operationFeeVar != 0 ? Math.ceil((operationFeeMin / operationFeeVar) * 10 ** 5) : 0,
      y: operationFeeMin,
    };

    let data = [P1, P2];
    if (maxVarFee > operationFeeMin) {
      const P3 = { x: stakeMax, y: maxVarFee };
      data = [...data, P3];
    }

    setData(data);
  }, [form]);

  return (
    <div className="rounded-lg bg-background-light py-6 xl:px-4">
      <ValidatorAdConfigGraph chartData={data} chartConfig={chartConfig} xKey="x" yKey="y" />
    </div>
  );
};

export default GraphWidget;
